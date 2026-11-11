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
from live_authorization import verify_authority, claim
from real_transport import RealTransport


def configuration(args):
    return dict(live=True, authorization_file=str(args.authorization.absolute()),
                aggregate_authorization_file=str(args.aggregate_authorization.absolute()),
                operator_public_key=str(args.operator_public_key.absolute()),
                ledger_path=str(args.ledger.absolute()), run_id=args.run,
                contract_path=str(args.contract.absolute()))


def build_gateway(root, contract, ledger, run, transport, token, abort):
    d = contract.data
    rate = lambda key: int((Decimal(d[key])*1000000).to_integral_value(rounding=ROUND_CEILING))
    policy = Policy('OpenAI', d['model'], 'https://api.openai.com/v1/chat/completions',
                    ('api.openai.com',), 4, 120000, rate('input_usd_per_million'),
                    rate('output_usd_per_million'), d['max_input_tokens'], 512, 512)
    artifacts = Artifacts(root, offline=False, secrets=(token,))
    artifacts.write('policy.json', canonical(asdict(policy)))
    bounds = threading.local()

    def checked_transport(url, raw):
        ledger.remaining_seconds('coding', run)
        transport.timeout = min(60, ledger.remaining_seconds('coding', run))
        status, kind, response = transport(url, raw)
        from gateway import validate_response, length_truncated
        usage = validate_response(response, kind, d['model']) if status == 200 else []
        if len(usage) != 1 or length_truncated(response, kind):
            raise ValueError('uncertain_live_cost_or_response')
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
            raise ValueError('usage_exceeds_reserved_bound')
        return status, kind, response

    gateway = guard_gateway(Gateway(policy, artifacts, checked_transport), ledger, 'coding', run,
                            cost_bound=lambda _: bounds.value['reserved_micro_usd'],
                            token_bound=lambda _: (bounds.value['input_token_upper_bound'], bounds.value['output_token_upper_bound']),
                            estimator=contract.estimate)
    original = gateway.handle

    def handle(raw):
        try:
            if abort.is_set():
                raise ValueError('run_aborted')
            normalized, bounds.value = contract.prepare(raw)
            result = original(normalized)
            if result[0] != 200:
                gateway.budget.failed = True
                abort.set()
            return result
        except Exception:
            gateway.budget.failed = True
            abort.set()
            raise
    gateway.handle = handle
    return gateway


def execute(args):
    if not args.arm_live:
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
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    if args.ledger.exists():
        from live_authorization import private_file
        private_file(args.ledger)
    else:
        fd = os.open(args.ledger, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    ledger = AggregateBudget(args.ledger, experiment_contract=data)
    claim(ledger, authority, aggregate)
    ledger.control_run('coding', args.run, 'start')
    abort = threading.Event()
    server = None
    timer = threading.Timer(ledger.remaining_seconds('coding', args.run), abort.set)
    timer.daemon = True
    transport = None
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
        transport = RealTransport(**config)
        gateway = build_gateway(audit, contract, ledger, args.run, transport, token, abort)
        server = inference_socket(root/'gateway.sock', gateway, token,
                                  normalize_request=lambda raw: contract.prepare(raw)[0])
        threading.Thread(target=server.serve_forever, daemon=True).start()
        timer.start()
        report = run_command(root/'gateway.sock', workspace,
                             coding_command(args.runtime, contract.data['model']),
                             mounts=[(ROOT/'live-agent.mts', '/eval/coding-agent.mts'),
                                     (token_path, '/run/local-token'), (objective, '/run/objective.txt'), *mounts],
                             timeout=ledger.remaining_seconds('coding', args.run), abort_event=abort)
        server.revoked.set()
        for field in ('stdout', 'stderr'):
            if token.encode() in report[field]:
                raise ValueError('gateway_token_in_agent_output')
            (root/('agent-'+field+'.txt')).write_bytes(report[field])
        if report['exit_code'] != 0 or report['timed_out'] or report['aborted'] or abort.is_set():
            raise RuntimeError('live_agent_failed_or_aborted')
        snapshot = ledger.snapshot()
        current_ids = {r['id'] for r in snapshot['reservations'] if r['stage'] == 'coding' and r['run'] == args.run}
        if not current_ids:
            raise RuntimeError('no_model_request')
        states = {event['reservation_id']: event['state'] for event in snapshot['transitions']}
        if any(states.get(ident) != 'SETTLED' for ident in current_ids):
            raise RuntimeError('unsettled_live_request')
        candidate = workspace/'solution.py'
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
        if grade.get('infrastructure_failure'):
            raise RuntimeError('independent_grader_failed')
        result = {'classification': 'LIVE_MODEL_CODING', 'run': args.run,
                  'independent_acceptance': grade, 'ledger': ledger.snapshot()}
        (root/'live-observation.json').write_bytes(canonical(result))
        ledger.control_run('coding', args.run, 'COMPLETE')
        return result
    except BaseException:
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
    parser.add_argument('--arm-live', action='store_true')
    parser.add_argument('--task', choices=fixture_binding()['canonical_order'], required=True)
    parser.add_argument('--run', required=True)
    for name in ('runtime', 'output', 'ledger', 'authorization', 'aggregate-authorization', 'operator-public-key'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--contract', type=Path, default=ROOT/'experiment-parameters.json')
    args = parser.parse_args()
    try:
        result = execute(args)
        print(json.dumps({'run': result['run'], 'independent_acceptance': result['independent_acceptance']}))
    except Exception:
        # Do not emit exceptions containing paths, provider material or credentials.
        parser.exit(1, 'LIVE_REFUSED_OR_INCOMPLETE; no automatic retry; inspect private ledger\n')


if __name__ == '__main__':
    main()
