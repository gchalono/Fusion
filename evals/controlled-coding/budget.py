"""FNXC:ControlledCoding 2026-11-09-03:54:
The trusted gateway reserves worst-case charges before EACH transport attempt,
including planning, retries and compaction. BEGIN IMMEDIATE serializes writers;
FULL synchronous commits survive process interruption. Reservations are append
only and never refunded, including uncertain or interrupted requests. Usage,
price-based estimates and measured charges are separate append-only evidence.
This module cannot establish sole egress: live remains disabled pending recovery
of the Phase 2M supervisor and independent proof of its sandbox boundary.
"""
import json
import hashlib
import threading
import time
from dataclasses import asdict
import sqlite3
from pathlib import Path

CAP_MICRO_USD = 2_000_000
CODING_CAP_MICRO_USD = 150_000
CODING_CALL_CAP = 4


class AggregateBudget:
    def __init__(self, path, *, experiment_contract=None):
        self.path = str(Path(path).resolve())
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS experiment_contract (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS contract_no_update BEFORE UPDATE ON experiment_contract
                    BEGIN SELECT RAISE(ABORT,'immutable_contract'); END;
                CREATE TRIGGER IF NOT EXISTS contract_no_delete BEFORE DELETE ON experiment_contract
                    BEGIN SELECT RAISE(ABORT,'immutable_contract'); END;
                CREATE TABLE IF NOT EXISTS run_controls (stage TEXT NOT NULL,run TEXT NOT NULL,started REAL NOT NULL,deadline REAL NOT NULL,status TEXT NOT NULL,PRIMARY KEY(stage,run));
                CREATE TABLE IF NOT EXISTS request_bounds (reservation_id INTEGER PRIMARY KEY REFERENCES reservations(id), input_upper INTEGER NOT NULL, output_upper INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY, stage TEXT NOT NULL CHECK(stage IN ('planning','coding')),
                    run TEXT NOT NULL, upper_micro INTEGER NOT NULL CHECK(upper_micro>0),
                    created_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY, reservation_id INTEGER NOT NULL REFERENCES reservations(id),
                    provider_usage_json TEXT, estimated_charge_micro INTEGER,
                    measured_charge_micro INTEGER, evidence_ref TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS run_policies (
                    stage TEXT NOT NULL, run TEXT NOT NULL, policy_sha256 TEXT NOT NULL,
                    PRIMARY KEY(stage,run));
                CREATE TRIGGER IF NOT EXISTS policy_no_update BEFORE UPDATE ON run_policies
                    BEGIN SELECT RAISE(ABORT,'immutable_policy'); END;
                CREATE TRIGGER IF NOT EXISTS policy_no_delete BEFORE DELETE ON run_policies
                    BEGIN SELECT RAISE(ABORT,'immutable_policy'); END;
                CREATE TABLE IF NOT EXISTS transitions (
                    id INTEGER PRIMARY KEY, reservation_id INTEGER NOT NULL REFERENCES reservations(id),
                    state TEXT NOT NULL CHECK(state IN ('RESERVED','FORWARDED','SETTLED','UNCERTAIN')),
                    basis TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS transitions_no_update BEFORE UPDATE ON transitions
                    BEGIN SELECT RAISE(ABORT,'immutable_transition'); END;
                CREATE TRIGGER IF NOT EXISTS transitions_no_delete BEFORE DELETE ON transitions
                    BEGIN SELECT RAISE(ABORT,'immutable_transition'); END;
                CREATE TRIGGER IF NOT EXISTS reservations_no_update BEFORE UPDATE ON reservations
                    BEGIN SELECT RAISE(ABORT,'immutable_reservation'); END;
                CREATE TRIGGER IF NOT EXISTS reservations_no_delete BEFORE DELETE ON reservations
                    BEGIN SELECT RAISE(ABORT,'immutable_reservation'); END;
                CREATE TRIGGER IF NOT EXISTS observations_no_update BEFORE UPDATE ON observations
                    BEGIN SELECT RAISE(ABORT,'immutable_observation'); END;
                CREATE TRIGGER IF NOT EXISTS observations_no_delete BEFORE DELETE ON observations
                    BEGIN SELECT RAISE(ABORT,'immutable_observation'); END;
            ''')

        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT body FROM experiment_contract WHERE id=1').fetchone()
            body=json.dumps(experiment_contract,sort_keys=True,separators=(',',':')) if experiment_contract is not None else None
            if row and body and row[0]!=body:raise ValueError('experiment_contract_mismatch')
            if not row and body:db.execute('INSERT INTO experiment_contract VALUES (1,?)',(body,))
            self.contract=json.loads(row[0] if row else body) if row or body else None

    def control_run(self, stage, run, action):
        if not self.contract:raise ValueError('experiment_contract_required')
        now=time.time();limit=self.contract['planning_seconds' if stage=='planning' else 'coding_seconds']
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT started,deadline,status FROM run_controls WHERE stage=? AND run=?',(stage,run)).fetchone()
            if action=='start':
                if row:raise ValueError('run_exists_resume_required')
                db.execute('INSERT INTO run_controls VALUES (?,?,?,?,?)',(stage,run,now,now+limit,'ACTIVE'))
            elif action=='resume':
                if not row or row[2]!='INCOMPLETE' or not row[0]<=now<row[1]:raise ValueError('resume_denied')
                db.execute("UPDATE run_controls SET status='ACTIVE' WHERE stage=? AND run=?",(stage,run))
            elif action in ('INCOMPLETE','COMPLETE'):
                if not row:raise ValueError('unknown_run')
                db.execute('UPDATE run_controls SET status=? WHERE stage=? AND run=?',(action,stage,run))
            else:raise ValueError('unknown_control')

    def remaining_seconds(self, stage, run):
        with self.connect() as db:
            row=db.execute('SELECT started,deadline,status FROM run_controls WHERE stage=? AND run=?',(stage,run)).fetchone()
        now=time.time()
        if not row or row[2]!='ACTIVE' or now<row[0] or now>=row[1]:raise ValueError('run_not_active_or_deadline')
        return row[1]-now

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA foreign_keys=ON')
        return db

    def bind_policy(self, stage, run, policy_hash):
        if stage not in ('planning','coding') or not isinstance(run,str) or not run or len(policy_hash)!=64:
            raise ValueError('invalid_run_policy')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT policy_sha256 FROM run_policies WHERE stage=? AND run=?',(stage,run)).fetchone()
            if row and row[0]!=policy_hash:raise ValueError('run_policy_mismatch')
            if not row:db.execute('INSERT INTO run_policies VALUES (?,?,?)',(stage,run,policy_hash))

    def reserve(self, stage, run, upper_micro, *, token_bounds=None):
        if stage not in ('planning', 'coding') or not isinstance(run, str) or not run:
            raise ValueError('invalid_reservation')
        if type(upper_micro) is not int or not 0 < upper_micro <= CAP_MICRO_USD:
            raise ValueError('invalid_upper_bound')
        # A separate connection per attempt is necessary for threads/processes.
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            total = db.execute('SELECT COALESCE(SUM(upper_micro),0) FROM reservations').fetchone()[0]
            used, calls = db.execute('SELECT COALESCE(SUM(upper_micro),0), COUNT(*) FROM reservations WHERE stage=? AND run=?', (stage, run)).fetchone()
            if self.contract:
                allowed=self.contract['planning_run_ids' if stage=='planning' else 'coding_run_ids']
                if run not in allowed:raise ValueError('unregistered_experiment_run')
                control=db.execute('SELECT started,deadline,status FROM run_controls WHERE stage=? AND run=?',(stage,run)).fetchone()
                now=time.time()
                if not control or control[2]!='ACTIVE' or not control[0]<=now<control[1]:raise ValueError('run_deadline_or_inactive')
                stage_used=db.execute('SELECT COALESCE(SUM(upper_micro),0) FROM reservations WHERE stage=?',(stage,)).fetchone()[0]
                from contract import micro
                cap=micro(self.contract['planning_reserve_usd' if stage=='planning' else 'coding_allocation_usd'])
                if stage_used+upper_micro>cap:raise ValueError('stage_allocation_cap')
                request_cap=self.contract['planning_attempts_per_task' if stage=='planning' else 'coding_attempts_per_run']
                if calls>=request_cap:raise ValueError('experiment_request_cap')
                if token_bounds is None:raise ValueError('request_token_bounds_required')
                if any(type(x) is not int or x<0 for x in token_bounds):raise ValueError('invalid_token_bounds')
                from decimal import Decimal,ROUND_CEILING
                minimum=int((Decimal(token_bounds[0])*Decimal(self.contract['input_usd_per_million'])+Decimal(token_bounds[1])*Decimal(self.contract['output_usd_per_million'])).to_integral_value(rounding=ROUND_CEILING))
                if upper_micro<minimum:raise ValueError('under_reserved_request')
                if token_bounds[0]>self.contract['max_input_tokens'] or token_bounds[1]>self.contract['max_output_tokens']:raise ValueError('request_token_limit')
                if stage=='coding':
                    used_tokens=db.execute('SELECT COALESCE(SUM(b.input_upper+b.output_upper),0) FROM request_bounds b JOIN reservations r ON r.id=b.reservation_id WHERE r.stage=? AND r.run=?',(stage,run)).fetchone()[0]
                    if used_tokens+sum(token_bounds)>self.contract.get('frozen_coding_token_limit',16000):raise ValueError('frozen_coding_token_limit')
            if total+upper_micro > CAP_MICRO_USD:
                raise ValueError('aggregate_spend_cap')
            # FNXC:BlockerResolution 2026-11-09-18:27: Apply the operator's tighter
            # per-run cap without changing frozen fixtures or legacy ceilings.
            coding_cap=min(CODING_CAP_MICRO_USD,micro(self.contract['per_run_coding_cap_usd'])) if self.contract else CODING_CAP_MICRO_USD
            if stage == 'coding' and (used+upper_micro > coding_cap or calls >= CODING_CALL_CAP):
                raise ValueError('coding_run_cap')
            ident = db.execute('INSERT INTO reservations(stage,run,upper_micro) VALUES (?,?,?)', (stage, run, upper_micro)).lastrowid
            db.execute('INSERT INTO transitions(reservation_id,state,basis) VALUES (?,?,?)',(ident,'RESERVED','worst_case'))
            if token_bounds is not None:db.execute('INSERT INTO request_bounds VALUES (?,?,?)',(ident,*token_bounds))
        # Return only AFTER commit. Failed/uncertain commits never reach transport.
        return ident

    # FNXC:NativeIsolation 2026-11-09-04:44: Record durable lifecycle without refunds.
    def transition(self, ident, state, basis):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT state FROM transitions WHERE reservation_id=? ORDER BY id DESC LIMIT 1',(ident,)).fetchone()
            previous=row[0] if row else 'RESERVED'
            allowed={'RESERVED':{'FORWARDED','UNCERTAIN'},'FORWARDED':{'SETTLED','UNCERTAIN'},'SETTLED':set(),'UNCERTAIN':set()}
            if state not in allowed[previous] or not isinstance(basis,str) or not basis:
                raise ValueError('invalid_ledger_transition')
            db.execute('INSERT INTO transitions(reservation_id,state,basis) VALUES (?,?,?)',(ident,state,basis))

    def recover_uncertain(self):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            ids=db.execute("SELECT r.id FROM reservations r WHERE COALESCE((SELECT state FROM transitions t WHERE t.reservation_id=r.id ORDER BY t.id DESC LIMIT 1),'RESERVED') IN ('RESERVED','FORWARDED')").fetchall()
            for (ident,) in ids:
                db.execute('INSERT INTO transitions(reservation_id,state,basis) VALUES (?,?,?)',(ident,'UNCERTAIN','restart_unreconciled'))
        return len(ids)

    def observe(self, reservation_id, *, evidence_ref, provider_usage=None,
                estimated_charge_micro=None, measured_charge_micro=None):
        if type(reservation_id) is not int or not isinstance(evidence_ref, str) or not evidence_ref:
            raise ValueError('invalid_observation')
        for amount in (estimated_charge_micro, measured_charge_micro):
            if amount is not None and (type(amount) is not int or amount < 0):
                raise ValueError('invalid_charge')
        raw = None if provider_usage is None else json.dumps(provider_usage, allow_nan=False, sort_keys=True)
        with self.connect() as db:
            # Observations are evidence, never authorization or budget refunds.
            db.execute('INSERT INTO observations(reservation_id,provider_usage_json,estimated_charge_micro,measured_charge_micro,evidence_ref) VALUES (?,?,?,?,?)',
                       (reservation_id, raw, estimated_charge_micro, measured_charge_micro, evidence_ref))

    def snapshot(self):
        with self.connect() as db:
            db.execute('BEGIN')
            rows = [dict(zip(('id', 'stage', 'run', 'reserved_exposure_micro_usd', 'created_utc'), row))
                    for row in db.execute('SELECT * FROM reservations ORDER BY id')]
            observations = [dict(zip(('id', 'reservation_id', 'provider_reported_usage_json',
                                      'estimated_provider_charge_micro_usd', 'measured_provider_charge_micro_usd', 'evidence_ref'), row))
                            for row in db.execute('SELECT * FROM observations ORDER BY id')]
            events=[dict(zip(('id','reservation_id','state','basis'),row)) for row in db.execute('SELECT * FROM transitions ORDER BY id')]
        exposure = sum(r['reserved_exposure_micro_usd'] for r in rows)
        return {'cap_micro_usd': CAP_MICRO_USD, 'reserved_exposure_micro_usd': exposure,
                'remaining_reservable_micro_usd': CAP_MICRO_USD-exposure,
                'reservations': rows, 'observations': observations, 'transitions':events}


def guard_gateway(gateway, ledger, stage, run, *, cost_bound=None, estimator=None, token_bound=None):
    """Offline integration with the existing gateway; no new supervisor."""
    original = gateway.budget
    transport = gateway.transport
    active = threading.local()
    policy_hash=hashlib.sha256(json.dumps(asdict(gateway.policy),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    ledger.bind_policy(stage,run,policy_hash)
    class Guard:
        def __getattr__(self, name):
            return getattr(original, name)

        @property
        def failed(self):
            return original.failed

        @failed.setter
        def failed(self, value):
            original.failed = value

        def reserve(self, request):
            before = original.reserved
            try:
                attempt = original.reserve(request)
                exposure=cost_bound(request) if cost_bound else original.reserved-before
                reservation_id = ledger.reserve(stage, run, exposure,token_bounds=token_bound(request) if token_bound else None)
                active.ident=reservation_id
                # Audit linking must also succeed before transport is permitted.
                gateway.artifacts.write(f'aggregate-reservation-{attempt:04}.json',
                    json.dumps({'reservation_id': reservation_id, 'stage': stage, 'run': run,
                                'policy_sha256':policy_hash, 'attempt': attempt, 'reserved_exposure_micro_usd': exposure},
                               sort_keys=True).encode())
                return attempt
            except BaseException:
                original.failed = True
                raise
    def accounted_transport(url, raw):
        from gateway import validate_response, length_truncated
        ident=active.ident
        ledger.transition(ident,'FORWARDED','before_transport')
        try:
            status, content_type, response=transport(url,raw)
            usage=validate_response(response,content_type,gateway.policy.model) if status==200 else []
            # FNXC:RealModelReadiness 2026-11-10-04:59: Usage in an interrupted
            # SSE response is not completion evidence. No reservation is refunded.
            stream_complete='text/event-stream' not in content_type or response.rstrip().endswith(b'data: [DONE]')
            if status!=200 or len(usage)!=1 or not stream_complete or length_truncated(response,content_type):
                ledger.transition(ident,'UNCERTAIN','missing_usage_or_incomplete_response')
            else:
                u=usage[-1]
                if any(type(u.get(k)) is not int or u[k]<0 for k in ('prompt_tokens','completion_tokens')):
                    ledger.transition(ident,'UNCERTAIN','invalid_usage')
                else:
                    estimate=(u['prompt_tokens']*gateway.policy.input_price_micro_per_million+u['completion_tokens']*gateway.policy.output_price_micro_per_million+999999)//1000000
                    if estimator:estimate=estimator(u)
                    ledger.observe(ident,evidence_ref='gateway-attempt:'+str(ident),provider_usage=u,estimated_charge_micro=estimate)
                    active.settlement='estimated_from_provider_reported_usage'
            return status,content_type,response
        except BaseException:
            try: ledger.transition(ident,'UNCERTAIN','transport_or_accounting_interrupted')
            except Exception: pass
            raise
    handle=gateway.handle
    def durable_handle(raw):
        active.ident=None
        active.settlement=None
        try:
            response=handle(raw)
            if active.settlement:
                ledger.transition(active.ident,'SETTLED',active.settlement)
            return response
        except BaseException:
            if active.ident is not None:
                try:ledger.transition(active.ident,'UNCERTAIN','request_or_artifact_incomplete')
                except Exception:pass  # Exposure is retained; recovery handles DB/write failure.
            raise
    gateway.handle=durable_handle
    gateway.transport = accounted_transport
    gateway.budget = Guard()
    return gateway
