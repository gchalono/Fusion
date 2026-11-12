"""Run 5 continuation; all earlier authority and exposure remain durable."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from contextlib import closing
import time

from contract import canonical, micro

RUN = 'parse-duration:C'
PREVIOUS_RUN = 'parse-duration:B'
RUN3_RUN = 'parse-duration:A'
TASK = 'parse-duration'
DESIGN = 'controlled-live-local-self-test-v1'
ROOT = Path(__file__).resolve().parent
CODE_FILES = ('live.py', 'live-agent.mts', 'live-agent-outcome.mjs',
              'self-test-session.mjs', 'execution.py', 'isolation.py',
              'sandbox_entry.py', 'security_filter.py', 'contract.py', 'budget.py', 'pilot.py',
              'independent.py', 'harness.py', 'acceptance_runner.py', 'acceptance_worker.py',
              'live_authorization.py', 'reliability_authorization.py', 'reliability_operator.py', 'real_transport.py',
              '../planning-collector/gateway.py')


def implementation_binding():
    files = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in CODE_FILES}
    return {'files': files, 'sha256': hashlib.sha256(canonical(files)).hexdigest()}


def _validate_prior_run(document, expected_run, prior_aggregate, root, expected_predecessor):
    if (document.get('kind') != 'coding-run'
            or document.get('run_id') != expected_run
            or document.get('task_id') != TASK
            or document.get('aggregate_nonce') != prior_aggregate.get('nonce')
            or document.get('contract_sha256') != root.get('contract_sha256')
            or document.get('ledger_path') != root.get('ledger_path')
            or document.get('experiment_design') != DESIGN
            or document.get('reliability_authorized') is not True
            or document.get('historical_phase2n_arm') is not False
            or document.get('predecessor_run_id') != expected_predecessor
            or document.get('authorized_spend_usd') != '0.12'
            or document.get('max_requests') != 4
            or document.get('max_seconds') != 300
            or document.get('provider_side_cap_confirmed') is not False
            or document.get('accept_no_provider_hard_cap') is not True):
        raise ValueError('reliability_historical_run_mismatch')
    if any(not isinstance(document.get(key), str)
           or not re.fullmatch('[0-9a-f]{64}', document[key])
           for key in ('implementation_sha256', 'fixture_sha256')):
        raise ValueError('reliability_historical_binding_missing')


def chain(config, aggregate):
    """Verify root -> B renewal -> Run 3 -> Run 4 -> fresh Run 5 authority."""
    from live_authorization import signed_document, validate_renewal
    if (config.get('reliability') is not True or config.get('followup')
            or config.get('run_id') != RUN or aggregate.get('reliability_version') != 3
            or type(aggregate.get('reliability_version')) is not int
            or aggregate.get('renewal_version') is not None
            or aggregate.get('renewal_run_id') != RUN
            or aggregate.get('budget_semantics') != 'cumulative-existing-ledger'):
        raise ValueError('reliability_scope_required')
    root = signed_document(config['original_aggregate_authorization_file'],
                           config['operator_public_key'], expired_predecessor=True)
    b_renewal = signed_document(config['previous_aggregate_authorization_file'],
                                config['operator_public_key'], expired_predecessor=True)
    validate_renewal(b_renewal, root, historical=True)
    run3_aggregate = signed_document(config['run3_reliability_aggregate_authorization_file'],
                                     config['operator_public_key'], expired_predecessor=True)
    run3 = signed_document(config['run3_run_authorization_file'],
                           config['operator_public_key'], expired_predecessor=True)
    run4_aggregate = signed_document(config['previous_reliability_aggregate_authorization_file'],
                                     config['operator_public_key'], expired_predecessor=True)
    run4 = signed_document(config['previous_run_authorization_file'],
                           config['operator_public_key'], expired_predecessor=True)
    digest = lambda value: hashlib.sha256(canonical(value)).hexdigest()
    root_fields = ('schema', 'kind', 'contract_sha256', 'ledger_path', 'authorized_spend_usd',
                   'accept_no_provider_hard_cap')
    if (run3_aggregate.get('reliability_version') != 1
            or type(run3_aggregate.get('reliability_version')) is not int
            or run3_aggregate.get('renewal_version') is not None
            or run3_aggregate.get('renewal_run_id') != RUN3_RUN
            or run3_aggregate.get('budget_semantics') != 'cumulative-existing-ledger'
            or run3_aggregate.get('continues_nonce') != b_renewal['nonce']
            or run3_aggregate.get('continues_sha256') != digest(b_renewal)
            or any(run3_aggregate.get(k) != root.get(k) for k in root_fields)
            or run4_aggregate.get('reliability_version') != 2
            or type(run4_aggregate.get('reliability_version')) is not int
            or run4_aggregate.get('renewal_version') is not None
            or run4_aggregate.get('renewal_run_id') != PREVIOUS_RUN
            or run4_aggregate.get('budget_semantics') != 'cumulative-existing-ledger'
            or run4_aggregate.get('continues_nonce') != run3_aggregate['nonce']
            or run4_aggregate.get('continues_sha256') != digest(run3_aggregate)
            or run4_aggregate.get('predecessor_run_nonce') != run3['nonce']
            or run4_aggregate.get('predecessor_run_sha256') != digest(run3)
            or run4.get('model') != run3.get('model')
            or any(run4_aggregate.get(k) != root.get(k) for k in root_fields)):
        raise ValueError('reliability_historical_aggregate_mismatch')
    _validate_prior_run(run3, RUN3_RUN, run3_aggregate, root, 'merge-intervals:B')
    _validate_prior_run(run4, PREVIOUS_RUN, run4_aggregate, root, RUN3_RUN)
    if (not b_renewal['expires_at'] <= run3_aggregate['issued_at']
            or not run3_aggregate['issued_at'] <= run3['issued_at'] < run3['expires_at'] <= run3_aggregate['expires_at']
            or not max(run3_aggregate['expires_at'], run3['expires_at']) <= run4_aggregate['issued_at']
            or not run4_aggregate['issued_at'] <= run4['issued_at'] < run4['expires_at'] <= run4_aggregate['expires_at']
            or not max(run4_aggregate['expires_at'], run4['expires_at']) <= aggregate['issued_at']
            or not aggregate['issued_at'] <= time.time() < aggregate['expires_at']
            or aggregate.get('continues_nonce') != run4_aggregate['nonce']
            or aggregate.get('continues_sha256') != digest(run4_aggregate)
            or aggregate.get('predecessor_run_nonce') != run4['nonce']
            or aggregate.get('predecessor_run_sha256') != digest(run4)
            or aggregate.get('nonce') in (root['nonce'], b_renewal['nonce'], run3_aggregate['nonce'], run4_aggregate['nonce'])):
        raise ValueError('reliability_chain_mismatch')
    if any(aggregate.get(k) != root.get(k) for k in root_fields):
        raise ValueError('reliability_changes_original_authority')
    return root, b_renewal, run3_aggregate, run3, run4_aggregate, run4


def receipts(db, config, aggregate, *, claimed=False):
    from live_authorization import verify_aggregate_receipts
    root, b_renewal, run3_aggregate, run3, run4_aggregate, run4 = chain(config, aggregate)
    verify_aggregate_receipts(db, b_renewal, root, claimed=True)
    digest = lambda value: hashlib.sha256(canonical(value)).hexdigest()
    if db.execute("SELECT nonce,digest,run FROM live_authority WHERE kind='aggregate-reliability'").fetchall() != [
            (run3_aggregate['nonce'], digest(run3_aggregate), 'aggregate-reliability:'+b_renewal['nonce'])]:
        raise ValueError('reliability_run3_aggregate_receipt_required')
    for previous_run, expected_id in ((run3, RUN3_RUN), (run4, PREVIOUS_RUN)):
        if db.execute("SELECT digest FROM live_authority WHERE kind='run' AND nonce=? AND run=?",
                      (previous_run['nonce'], expected_id)).fetchone() != (digest(previous_run),):
            raise ValueError('reliability_predecessor_run_unclaimed')
    continuation_receipts = db.execute(
        "SELECT nonce,digest,run FROM live_authority WHERE kind='aggregate-reliability-continuation' ORDER BY rowid").fetchall()
    run4_receipt = (run4_aggregate['nonce'], digest(run4_aggregate),
                    'aggregate-reliability-continuation:'+run3_aggregate['nonce'])
    current_receipt = (aggregate['nonce'], digest(aggregate),
                       'aggregate-reliability-continuation:'+run4_aggregate['nonce'])
    if continuation_receipts not in ([run4_receipt], [run4_receipt, current_receipt]):
        raise ValueError('reliability_continuation_fork_or_replay')
    collision = db.execute('SELECT kind,digest,run FROM live_authority WHERE nonce=?', (aggregate['nonce'],)).fetchone()
    expected_collision = ('aggregate-reliability-continuation', *current_receipt[1:])
    if collision and collision != expected_collision:
        raise ValueError('reliability_nonce_collision')
    if claimed and continuation_receipts != [run4_receipt, current_receipt]:
        raise ValueError('unclaimed_reliability_authority')
    return run4_aggregate


def verify_ledger(config, contract, run, aggregate, *, unused=False, experiment_data=None):
    from live_authorization import private_file
    from pilot import fixture_binding
    binding = fixture_binding(TASK)
    if (run.get('run_id') != RUN or run.get('task_id') != TASK
            or run.get('experiment_design') != DESIGN
            or run.get('reliability_authorized') is not True
            or run.get('historical_phase2n_arm') is not False
            or run.get('predecessor_run_id') != PREVIOUS_RUN
            or run.get('implementation_sha256') != implementation_binding()['sha256']
            or run.get('fixture_sha256') != binding['derived_fixture_sha256']):
        raise ValueError('reliability_design_or_implementation_mismatch')
    if not (aggregate['issued_at'] <= run['issued_at'] < run['expires_at'] <= aggregate['expires_at']):
        raise ValueError('reliability_run_authority_window_mismatch')
    path = private_file(config['ledger_path'])
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        row = db.execute('SELECT body FROM experiment_contract WHERE id=1').fetchone()
        stored = json.loads(row[0]) if row else {}
        if (canonical({k: stored.get(k) for k in contract.data}) != canonical(contract.data)
                or RUN not in stored.get('coding_run_ids', [])
                or (experiment_data is not None and canonical(stored) != canonical(experiment_data))):
            raise ValueError('reliability_immutable_contract_mismatch')
        receipts(db, config, aggregate)
        for identity, status in [('merge-intervals:A', 'INCOMPLETE'),
                                 ('merge-intervals:B', 'COMPLETE'),
                                 (RUN3_RUN, 'INCOMPLETE'), (PREVIOUS_RUN, 'INCOMPLETE')]:
            if (db.execute("SELECT status FROM run_controls WHERE stage='coding' AND run=?", (identity,)).fetchone() != (status,)
                    or db.execute("SELECT COUNT(*) FROM live_authority WHERE kind='run' AND run=?", (identity,)).fetchone()[0] != 1):
                raise ValueError('reliability_historical_runs_required')
        if db.execute("SELECT 1 FROM reservations r WHERE run='merge-intervals:B' AND (SELECT state FROM transitions WHERE reservation_id=r.id ORDER BY id DESC LIMIT 1) IS NOT 'SETTLED'").fetchone():
            raise ValueError('reliability_unsettled_predecessor')
        total = db.execute('SELECT COALESCE(SUM(upper_micro),0) FROM reservations').fetchone()[0]
        coding = db.execute("SELECT COALESCE(SUM(upper_micro),0) FROM reservations WHERE stage='coding'").fetchone()[0]
        if unused:
            if min(run['expires_at'], aggregate['expires_at']) < time.time()+300:
                raise ValueError('reliability_authority_expires_before_deadline')
            for table in ('run_controls', 'live_authority', 'reservations', 'run_policies'):
                if db.execute(f'SELECT 1 FROM {table} WHERE run=?', (RUN,)).fetchone():
                    raise ValueError('reliability_run_already_used')
            if db.execute('SELECT 1 FROM live_authority WHERE nonce=?', (run['nonce'],)).fetchone():
                raise ValueError('reliability_nonce_collision')
            if db.execute("SELECT 1 FROM run_controls WHERE status='ACTIVE'").fetchone():
                raise ValueError('reliability_active_run_conflict')
            if total+120000 > 2000000 or coding+120000 > micro(stored['coding_allocation_usd']):
                raise ValueError('reliability_insufficient_remaining_budget')
        return total
