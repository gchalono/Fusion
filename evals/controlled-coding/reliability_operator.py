"""Human-only commands. Importing/help/preflight never sign or launch a run."""
import argparse
import hashlib
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

from contract import Contract, canonical
from live_authorization import private_file, signed_document
from pilot import fixture_binding
from reliability_authorization import DESIGN, PREVIOUS_RUN, RUN, TASK, chain, implementation_binding, verify_ledger

ROOT = Path(__file__).resolve().parent
AGGREGATE_NAME = 'aggregate-self-test-005'
RUN_NAME = 'run-self-test-005'


def authority_directory(path):
    auth = path.resolve()
    info = auth.stat()
    if not auth.is_dir() or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('private_authority_directory_required')
    return auth


def command(args, mode):
    auth = authority_directory(args.authority_dir)
    return [sys.executable, '-B', str(ROOT/'live.py'), mode,
            *([] if mode == '--reliability-preflight' else ['--reliability']),
            '--task', TASK, '--run', RUN, '--runtime', str(ROOT.parents[1]),
            '--output', str(args.output.absolute()), '--ledger', str(auth/'experiment.db'),
            '--authorization', str(auth/(RUN_NAME+'.json')),
            '--aggregate-authorization', str(auth/(AGGREGATE_NAME+'.json')),
            '--previous-aggregate-authorization', str(auth/'aggregate-renewal-B.json'),
            '--original-aggregate-authorization', str(auth/'aggregate.json'),
            '--previous-reliability-aggregate-authorization', str(auth/'aggregate-self-test-004.json'),
            '--previous-run-authorization', str(auth/'run-self-test-004.json'),
            '--run3-aggregate-authorization', str(auth/'aggregate-self-test-003.json'),
            '--run3-run-authorization', str(auth/'run-self-test-003.json'),
            '--operator-public-key', str(auth/'operator.pub'), '--contract', str(auth/'contract.json')]


def sign(args):
    if not sys.stdin.isatty():
        raise ValueError('private_operator_terminal_required')
    auth = authority_directory(args.authority_dir)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError('new_output_required')
    for name in (AGGREGATE_NAME, RUN_NAME):
        for suffix in ('.payload', '.sig', '.json'):
            path = auth/(name+suffix)
            if path.exists() or path.is_symlink():
                raise ValueError('existing_signing_artifacts_stop_do_not_overwrite')
    private_file(auth/'provider-key')  # Metadata only.
    private_file(auth/'operator-private.pem')  # Metadata only; OpenSSL signs in the human terminal.
    contract = Contract(auth/'contract.json')
    original = signed_document(auth/'aggregate.json', auth/'operator.pub', expired_predecessor=True)
    run4_aggregate = signed_document(auth/'aggregate-self-test-004.json', auth/'operator.pub', expired_predecessor=True)
    run4 = signed_document(auth/'run-self-test-004.json', auth/'operator.pub', expired_predecessor=True)
    if (original['contract_sha256'] != contract.sha256
            or original['ledger_path'] != str(auth/'experiment.db')):
        raise ValueError('original_contract_and_ledger_required')
    availability = input('Current exact-model availability verification reference: ').strip()
    pricing = input('Current conservative original-price verification reference: ').strip()
    if not availability or not pricing:
        raise ValueError('current_verification_references_required')
    acknowledgment = 'AUTHORIZE FRESH SELF-TEST RUN WITHIN THE SAME CUMULATIVE TWO DOLLARS WITHOUT PROVIDER HARD CAP'
    if input('Type '+acknowledgment+': ') != acknowledgment:
        raise ValueError('operator_declined')
    now = int(time.time())
    aggregate = dict(original, issued_at=now, expires_at=now+3600,
                     nonce=secrets.token_hex(24), reliability_version=3,
                     continues_nonce=run4_aggregate['nonce'],
                     continues_sha256=hashlib.sha256(canonical(run4_aggregate)).hexdigest(),
                     predecessor_run_nonce=run4['nonce'],
                     predecessor_run_sha256=hashlib.sha256(canonical(run4)).hexdigest(),
                     renewal_run_id=RUN, budget_semantics='cumulative-existing-ledger')
    run = dict(schema='fusion-live-v1', test_double=False, issued_at=now, expires_at=now+3600,
               nonce=secrets.token_hex(24), kind='coding-run',
               aggregate_nonce=aggregate['nonce'], contract_sha256=contract.sha256,
               ledger_path=str(auth/'experiment.db'), authorized_spend_usd='0.12',
               run_id=RUN, task_id=TASK, live_authorized=True, reliability_authorized=True,
               experiment_design=DESIGN, historical_phase2n_arm=False,
               predecessor_run_id=PREVIOUS_RUN,
               implementation_sha256=implementation_binding()['sha256'],
               fixture_sha256=fixture_binding(TASK)['derived_fixture_sha256'],
               model=contract.data['model'], approved_hosts=['api.openai.com'],
               provider_side_cap_confirmed=False, accept_no_provider_hard_cap=True,
               model_availability_verified=True, model_availability_evidence=availability,
               pricing_verified=True, pricing_verification_evidence=pricing,
               max_requests=4, max_seconds=300, key_file=str(auth/'provider-key'))
    config = dict(reliability=True, followup=False, run_id=RUN,
                  ledger_path=run['ledger_path'], operator_public_key=str(auth/'operator.pub'),
                  original_aggregate_authorization_file=str(auth/'aggregate.json'),
                  previous_aggregate_authorization_file=str(auth/'aggregate-renewal-B.json'),
                  run3_reliability_aggregate_authorization_file=str(auth/'aggregate-self-test-003.json'),
                  run3_run_authorization_file=str(auth/'run-self-test-003.json'),
                  previous_reliability_aggregate_authorization_file=str(auth/'aggregate-self-test-004.json'),
                  previous_run_authorization_file=str(auth/'run-self-test-004.json'))
    chain(config, aggregate)
    retained = verify_ledger(config, contract, run, aggregate, unused=True)
    print('Retained reserved micro-USD:', retained)
    print('Bound implementation SHA256:', run['implementation_sha256'])
    os.umask(0o077)
    for name, payload in ((AGGREGATE_NAME, aggregate), (RUN_NAME, run)):
        message = auth/(name+'.payload')
        with message.open('xb') as output:
            output.write(canonical(payload))
        result = subprocess.run(['openssl', 'pkeyutl', '-sign', '-rawin',
                                 '-inkey', str(auth/'operator-private.pem'), '-in', str(message)],
                                capture_output=True, timeout=300)
        if result.returncode or len(result.stdout) != 64:
            raise ValueError('human_signing_failed_preserve_partial_artifacts')
        with (auth/(name+'.sig')).open('xb') as output:
            output.write(result.stdout)
        with (auth/(name+'.json')).open('xb') as output:
            output.write(canonical(dict(payload=payload, signature=result.stdout.hex())))
    print('Two new documents signed. Ledger and prior documents unchanged. Run preflight next; no launch performed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['sign', 'preflight', 'launch'])
    parser.add_argument('--authority-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == 'sign':
            sign(args)
        elif args.action == 'preflight':
            subprocess.run(command(args, '--reliability-preflight'), check=True)
        else:
            if not sys.stdin.isatty():
                raise ValueError('private_operator_terminal_required')
            subprocess.run(command(args, '--reliability-preflight'), check=True)
            if input('Type LAUNCH ONE FRESH SELF-TEST RUN: ') != 'LAUNCH ONE FRESH SELF-TEST RUN':
                raise ValueError('operator_declined')
            subprocess.run(command(args, '--arm-live'), check=True)
    except Exception:
        parser.exit(1, 'OPERATOR_STEP_REFUSED; preserve files and inspect privately; no automatic retry\n')


if __name__ == '__main__':
    main()
