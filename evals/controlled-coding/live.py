"""Explicitly armed, single-run live coding. No missions, retries or resume.

The gateway, authority, ledger and credential stay in the trusted process. Only
an inference socket, its limited token, public runtime and frozen objective enter
the coding namespace. A fresh no-network sandbox independently grades the patch.
"""
import argparse
import difflib
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
import threading
from dataclasses import asdict
from decimal import Decimal, ROUND_CEILING

from pilot import fixture_binding, ROOT, Gateway, Policy, Artifacts
from budget import AggregateBudget, guard_gateway
from contract import Contract, canonical
from execution import run_command, runtime_mounts, coding_command
from independent import evaluate_patch
from isolation import inference_socket
from live_authorization import verify_authority, verify_followup_ledger, renewal_predecessor, claim
from real_transport import RealTransport


def _exception_family(error):
    if isinstance(error, TypeError): return 'type_error'
    if isinstance(error, ValueError): return 'value_error'
    if isinstance(error, TimeoutError): return 'timeout'
    if isinstance(error, OSError): return 'os_error'
    return 'other_error'


def _write_failure_diagnostic(root, run, stage, error):
    """Persist only fixed classifications; never serialize exception text."""
    allowed_stages = {'output_setup', 'transport_setup', 'gateway_setup', 'socket_setup',
                      'agent_execution', 'termination_record', 'agent_output',
                      'self_test_validation', 'candidate_validation', 'grading', 'completion'}
    if stage not in allowed_stages:
        stage = 'unknown_stage'
    family = _exception_family(error)
    code = 'transport_setup_type_error' if stage == 'transport_setup' and family == 'type_error' else f'{stage}_{family}'
    payload = canonical({'classification': 'LIVE_FAILURE_DIAGNOSTIC', 'run': run,
                         'failure_stage': stage, 'failure_code': code,
                         'exception_family': family,
                         'termination_record_written': (Path(root)/'termination.json').is_file()})
    path = Path(root)/'failure-diagnostic.json'
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
    directory = os.open(root, os.O_DIRECTORY)
    try: os.fsync(directory)
    finally: os.close(directory)


def configuration(args):
    config = dict(live=True, authorization_file=str(args.authorization.absolute()),
                aggregate_authorization_file=str(args.aggregate_authorization.absolute()),
                operator_public_key=str(args.operator_public_key.absolute()),
                ledger_path=str(args.ledger.absolute()), run_id=args.run,
                followup=getattr(args, 'followup', False),
                reliability=getattr(args, 'reliability', False),
                contract_path=str(args.contract.absolute()))
    if getattr(args, 'previous_aggregate_authorization', None) is not None:
        config['previous_aggregate_authorization_file'] = str(args.previous_aggregate_authorization.absolute())
    if getattr(args, 'original_aggregate_authorization', None) is not None:
        config['original_aggregate_authorization_file'] = str(args.original_aggregate_authorization.absolute())
    for arg_name, config_name in (
            ('previous_reliability_aggregate_authorization', 'previous_reliability_aggregate_authorization_file'),
            ('previous_run_authorization', 'previous_run_authorization_file'),
            ('run3_aggregate_authorization', 'run3_reliability_aggregate_authorization_file'),
            ('run3_run_authorization', 'run3_run_authorization_file')):
        if getattr(args, arg_name, None) is not None:
            config[config_name] = str(getattr(args, arg_name).absolute())
    return config


def build_gateway(root, contract, ledger, run, transport, token, abort):
    d = contract.data
    rate = lambda key: int((Decimal(d[key])*1000000).to_integral_value(rounding=ROUND_CEILING))
    policy = Policy('OpenAI', d['model'], 'https://api.openai.com/v1/chat/completions',
                    ('api.openai.com',), 4, 120000, rate('input_usd_per_million'),
                    rate('output_usd_per_million'), d['max_input_tokens'], 512, 512)
    artifacts = Artifacts(root, offline=False, secrets=(token,))
    artifacts.write('policy.json', canonical(asdict(policy)))
    bounds = threading.local()

    def response_failure(code, **details):
        error = ValueError(code)
        error.safe_details = details
        raise error

    def checked_transport(url, raw):
        ledger.remaining_seconds('coding', run)
        transport.timeout = min(60, ledger.remaining_seconds('coding', run))
        status, kind, response = transport(url, raw)
        from gateway import validate_response, length_truncated
        if status != 200:
            response_failure('provider_http_error', http_status=status)
        usage = validate_response(response, kind, d['model'])
        if length_truncated(response, kind):
            response_failure('provider_output_truncated', http_status=status)
        if len(usage) != 1:
            response_failure('provider_usage_missing_or_ambiguous', http_status=status, usage_records=len(usage))
        if 'text/event-stream' in kind:
            if not response.rstrip().endswith(b'data: [DONE]'):
                raise ValueError('incomplete_live_stream')
            frames = [json.loads(line[5:].strip()) for line in response.decode().splitlines()
                      if line.startswith('data:') and line[5:].strip() != '[DONE]']
        else:
            frames = [json.loads(response)]
        finishes = [choice.get('finish_reason') for frame in frames for choice in frame.get('choices', [])
                    if choice.get('finish_reason') is not None]
        if finishes not in (['stop'], ['tool_calls']):
            raise ValueError('incomplete_live_response')
        u = usage[-1]
        contract.estimate(u)
        b = bounds.value
        if (u['prompt_tokens'] > b['input_token_upper_bound']
                or u['completion_tokens'] > b['output_token_upper_bound']):
            response_failure('usage_exceeds_reserved_bound', prompt_tokens=u['prompt_tokens'],
                             completion_tokens=u['completion_tokens'], **{
                                 k: b[k] for k in ('input_token_upper_bound', 'output_token_upper_bound')})
        return status, kind, response

    gateway = guard_gateway(Gateway(policy, artifacts, checked_transport), ledger, 'coding', run,
                            cost_bound=lambda _: bounds.value['reserved_micro_usd'],
                            token_bound=lambda _: (bounds.value['input_token_upper_bound'], bounds.value['output_token_upper_bound']),
                            estimator=contract.estimate)
    original = gateway.handle
    gateway.failure_code = None

    def handle(raw):
        try:
            if abort.is_set():
                raise ValueError('run_aborted')
            normalized, bounds.value = contract.prepare(raw)
            result = original(normalized)
            if result[0] != 200:
                gateway.failure_code = gateway.last_failure_code or 'gateway_failure'
                gateway.budget.failed = True
                abort.set()
            return result
        except Exception as error:
            from gateway import safe_failure_code
            if gateway.failure_code is None:
                gateway.failure_code = safe_failure_code(error, 'gateway_failure')
            gateway.budget.failed = True
            abort.set()
            raise
    gateway.handle = handle
    return gateway


def execute(args, *, preflight=False):
    if not preflight and not args.arm_live:
        raise ValueError('explicit_arm_live_required')
    config = configuration(args)
    contract = Contract(args.contract)
    authority, aggregate = verify_authority(config, contract)
    binding = fixture_binding(args.task)
    if (authority.get('fixture_sha256') != binding['derived_fixture_sha256']
            or authority.get('task_id') != args.task):
        raise ValueError('authorization_fixture_binding')
    for path in (args.runtime/'node_modules/tsx/dist/loader.mjs', args.runtime/'packages/core/dist/index.js'):
        if not path.is_file():
            raise ValueError('runtime_dependencies_not_built')
    root = args.output.absolute()
    if root.exists() or root.is_symlink():
        raise ValueError('new_output_required')
    # Neither credentials nor control-plane documents may appear under any mount.
    mounts = runtime_mounts(args.runtime)
    public = [Path('/usr'), Path('/lib'), Path('/lib64'), Path('/bin'),
              *[Path(source).resolve() for source, _ in mounts]]
    for executable in (sys.executable, shutil.which('node')):
        if executable:
            public.append(Path(executable).resolve().parent.parent)
    if any(root.resolve().is_relative_to(p.resolve()) for p in public):
        raise ValueError('private_output_in_public_mount')
    protected = [Path(authority['key_file']), args.ledger, args.authorization,
                 args.aggregate_authorization, args.operator_public_key, args.contract]
    if config.get('previous_aggregate_authorization_file'):
        protected.append(Path(config['previous_aggregate_authorization_file']))
    if config.get('original_aggregate_authorization_file'):
        protected.append(Path(config['original_aggregate_authorization_file']))
    for key in ('previous_reliability_aggregate_authorization_file', 'previous_run_authorization_file',
                'run3_reliability_aggregate_authorization_file', 'run3_run_authorization_file'):
        if config.get(key):
            protected.append(Path(config[key]))
    for private in protected:
        if private.is_symlink() or any(private.resolve().is_relative_to(p.resolve()) for p in public):
            raise ValueError('private_material_in_public_mount')
        if private.resolve().is_relative_to(root.resolve()):
            raise ValueError('private_material_in_output')
    # A fixed signed ledger path persists across fresh output directories. Existing
    # ledgers must have exactly the registered contract; never replace history.
    data = dict(contract.data, planning_run_ids=binding['canonical_order'],
                coding_run_ids=[t+':'+a for t in binding['canonical_order'] for a in 'ABC'],
                frozen_coding_token_limit=16000, fixture_manifest_sha256=binding['frozen_manifest_sha256'])
    if args.run not in data['coding_run_ids'] or args.run.split(':')[0] != args.task:
        raise ValueError('unregistered_coding_run')
    retained = None
    if config['reliability']:
        from reliability_authorization import verify_ledger
        retained = verify_ledger(config, contract, authority, aggregate,
                                 unused=True, experiment_data=data)
    if config['followup']:
        retained = verify_followup_ledger(config, contract, authority, aggregate,
                                         unused=True, experiment_data=data)
    if preflight:
        # First-run preparation only: no ledger bootstrap, approval consumption,
        # credential contents, output creation or transport/network dispatch.
        if not config['followup'] and not config['reliability']:
            if args.run != 'merge-intervals:A' or args.task != 'merge-intervals':
                raise ValueError('first_run_preflight_only')
            if args.ledger.exists() or args.ledger.is_symlink():
                raise ValueError('first_run_ledger_already_exists')
        info = args.ledger.parent.stat()
        if not args.ledger.parent.is_dir() or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('private_ledger_directory_required')
        from ctypes.util import find_library
        if not shutil.which('bwrap') or not shutil.which('node') or not find_library('seccomp'):
            raise ValueError('sandbox_dependencies_required')
        return {'classification': ('RELIABILITY_PREFLIGHT_VERIFIED_NO_EXECUTION' if config['reliability'] else 'FOLLOWUP_PREFLIGHT_VERIFIED_NO_EXECUTION' if config['followup'] else 'PREFLIGHT_VERIFIED_NO_EXECUTION'), 'run': args.run,
                'experiment_design': authority.get('experiment_design', 'first-objective-only-live-run'),
                'retained_reserved_micro_usd': retained,
                'aggregate_renewal': authority['aggregate_nonce'] == aggregate['nonce'] and aggregate.get('renewal_version') == 1,
                'provider_hard_cap_confirmed': authority['provider_side_cap_confirmed'],
                'implementation_sha256': authority.get('implementation_sha256'),
                'internal_aggregate_cap_usd': '2.00', 'internal_per_run_cap_usd': '0.12',
                'max_requests': 4, 'max_seconds': 300}
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    if args.ledger.exists():
        from live_authorization import private_file
        private_file(args.ledger)
    else:
        fd = os.open(args.ledger, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    ledger = AggregateBudget(args.ledger, experiment_contract=data)
    previous = None if config['reliability'] else renewal_predecessor(config, aggregate)
    if config['reliability']:
        claim(ledger, authority, aggregate, reliability_config=config)
    elif previous is None:
        claim(ledger, authority, aggregate)
    else:
        claim(ledger, authority, aggregate, previous_aggregate=previous)
    ledger.control_run('coding', args.run, 'start')
    abort = threading.Event()
    server = None
    timer = threading.Timer(ledger.remaining_seconds('coding', args.run), abort.set)
    timer.daemon = True
    transport = None
    stage = 'output_setup'
    try:
        root.mkdir(mode=0o700, parents=True, exist_ok=False)
        workspace = root/'workspace'; workspace.mkdir()
        initial = ROOT/'fixtures'/args.task/'initial/solution.py'
        shutil.copyfile(initial, workspace/'solution.py')
        objective = root/'objective.txt'
        objective.write_text((ROOT/'fixtures'/args.task/'objective.txt').read_text())
        token = secrets.token_hex(32)
        token_path = root/'local-token'; token_path.write_text(token); token_path.chmod(0o600)
        audit = root/'gateway'; audit.mkdir()
        stage = 'transport_setup'
        transport = RealTransport(**config)
        stage = 'gateway_setup'
        gateway = build_gateway(audit, contract, ledger, args.run, transport, token, abort)
        stage = 'socket_setup'
        server = inference_socket(root/'gateway.sock', gateway, token,
                                  normalize_request=lambda raw: contract.prepare(raw)[0])
        threading.Thread(target=server.serve_forever, daemon=True).start()
        timer.start()
        stage = 'agent_execution'
        report = run_command(root/'gateway.sock', workspace,
                             coding_command(args.runtime, contract.data['model']),
                             mounts=[(ROOT/'live-agent.mts', '/eval/coding-agent.mts'),
                                     (ROOT/'live-agent-outcome.mjs', '/eval/live-agent-outcome.mjs'),
                                     (ROOT/'self-test-session.mjs', '/eval/self-test-session.mjs'),
                                     (token_path, '/run/local-token'), (objective, '/run/objective.txt'), *mounts],
                             timeout=ledger.remaining_seconds('coding', args.run), abort_event=abort)
        stage = 'termination_record'
        # Save scalar supervisor evidence even when the agent fails before grading.
        (root/'termination.json').write_bytes(canonical({
            'classification': 'CODING_PROCESS_TERMINATION',
            'exit_code': report['exit_code'], 'timed_out': report['timed_out'],
            'aborted': report['aborted'], 'elapsed_seconds': report['elapsed_seconds'],
            'gateway_aborted': abort.is_set(), 'gateway_failure_code': gateway.failure_code,
            'gateway_attempts': gateway.budget.calls,
        }))
        server.revoked.set()
        stage = 'agent_output'
        for field in ('stdout', 'stderr'):
            if token.encode() in report[field]:
                raise ValueError('gateway_token_in_agent_output')
            (root/('agent-'+field+'.txt')).write_bytes(report[field])
        if report['exit_code'] != 0 or report['timed_out'] or report['aborted'] or abort.is_set():
            raise RuntimeError('live_agent_failed_or_aborted')
        local_check = None
        if config['reliability']:
            stage = 'self_test_validation'
            audits = [line[len(b'LIVE_AGENT_AUDIT '):] for line in report['stdout'].splitlines()
                      if line.startswith(b'LIVE_AGENT_AUDIT ')]
            if len(audits) != 1:
                raise ValueError('reliability_live_audit_required')
            audit = json.loads(audits[0])
            local_check = audit.get('localCheck', {})
            if (audit.get('test_double') is not False or audit.get('runtime') != 'pi'
                    or audit.get('model') != contract.data['model']
                    or local_check.get('localSelfTest') != 'passed'
                    or type(local_check.get('repairs')) is not int
                    or local_check['repairs'] not in (0, 1)):
                raise ValueError('reliability_live_self_test_required')
        snapshot = ledger.snapshot()
        current_ids = {r['id'] for r in snapshot['reservations'] if r['stage'] == 'coding' and r['run'] == args.run}
        if not current_ids:
            raise RuntimeError('no_model_request')
        states = {event['reservation_id']: event['state'] for event in snapshot['transitions']}
        if any(states.get(ident) != 'SETTLED' for ident in current_ids):
            raise RuntimeError('unsettled_live_request')
        candidate = workspace/'solution.py'
        stage = 'candidate_validation'
        if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_size > 1000000:
            raise ValueError('invalid_candidate')
        raw = candidate.read_bytes()
        if token.encode() in raw:
            raise ValueError('gateway_token_in_candidate')
        patch = ''.join(difflib.unified_diff(initial.read_text().splitlines(True), raw.decode().splitlines(True), fromfile='a/solution.py', tofile='b/solution.py'))
        (root/'candidate.patch').write_text(patch)
        # Grading keeps its independent boundary and also fits within the run's
        # remaining deadline. Default offline grading retains its 30-second cap.
        grade = evaluate_patch(args.task, patch, root/'independent-check',
                               timeout=min(30, ledger.remaining_seconds('coding', args.run)))
        stage = 'grading'
        if grade.get('infrastructure_failure'):
            raise RuntimeError('independent_grader_failed')
        result = {'classification': 'LIVE_MODEL_CODING', 'run': args.run,
                  'experiment_design': authority.get('experiment_design', 'first-objective-only-live-run'),
                  'historical_phase2n_arm': False,
                  'independent_acceptance': grade, 'ledger': ledger.snapshot()}
        if config['reliability']:
            result['local_self_test'] = local_check
            result['implementation_sha256'] = authority['implementation_sha256']
        (root/'live-observation.json').write_bytes(canonical(result))
        stage = 'completion'
        ledger.control_run('coding', args.run, 'COMPLETE')
        return result
    except BaseException as error:
        try:
            _write_failure_diagnostic(root, args.run, stage, error)
        except OSError:
            # Preserve the original failure and ledger recovery path.
            pass
        abort.set()
        ledger.recover_uncertain()
        ledger.control_run('coding', args.run, 'INCOMPLETE')
        raise
    finally:
        timer.cancel()
        if server:
            server.revoked.set(); server.shutdown(); server.server_close()
        if transport:
            transport.abort()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--arm-live', action='store_true')
    mode.add_argument('--preflight', action='store_true', help='Read-only first-run checks; no credential contents or paid dispatch')
    mode.add_argument('--followup-preflight', action='store_true', help='Read-only B follow-up checks against the original ledger')
    mode.add_argument('--reliability-preflight', action='store_true', help='Read-only fresh-task self-test experiment checks')
    parser.add_argument('--followup', action='store_true', help='Use explicitly signed objective-only B follow-up authority')
    parser.add_argument('--reliability', action='store_true', help='Use explicitly signed parse-duration self-test experiment authority')
    parser.add_argument('--task', choices=fixture_binding()['canonical_order'], required=True)
    parser.add_argument('--run', required=True)
    for name in ('runtime', 'output', 'ledger', 'authorization', 'aggregate-authorization', 'operator-public-key'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--contract', type=Path, default=ROOT/'experiment-parameters.json')
    parser.add_argument('--previous-aggregate-authorization', type=Path,
                        help='Expired original aggregate, signature-checked only as renewal continuity evidence')
    parser.add_argument('--original-aggregate-authorization', type=Path,
                        help='Original expired root for the fresh-task continuation chain')
    parser.add_argument('--previous-reliability-aggregate-authorization', type=Path,
                        help='Expired Run 4 aggregate, verified as continuation history')
    parser.add_argument('--previous-run-authorization', type=Path,
                        help='Expired Run 4 authorization, verified against its ledger receipt')
    parser.add_argument('--run3-aggregate-authorization', type=Path,
                        help='Expired Run 3 aggregate, verified as historical chain evidence')
    parser.add_argument('--run3-run-authorization', type=Path,
                        help='Expired Run 3 authorization, verified against its ledger receipt')
    args = parser.parse_args()
    if args.followup_preflight:
        args.followup = True
    if args.reliability_preflight:
        args.reliability = True
    if args.followup and args.reliability:
        parser.error('followup and reliability are separate experiment designs')
    if args.preflight and (args.followup or args.reliability):
        parser.error('--preflight is first-run only; use --followup-preflight')
    try:
        preflight = args.preflight or args.followup_preflight or args.reliability_preflight
        result = execute(args, preflight=preflight)
        print(json.dumps(result if preflight else {'run': result['run'], 'independent_acceptance': result['independent_acceptance']}))
    except Exception:
        # Do not emit exceptions containing paths, provider material or credentials.
        parser.exit(1, 'LIVE_REFUSED_OR_INCOMPLETE; no automatic retry; inspect private ledger\n')


if __name__ == '__main__':
    main()
