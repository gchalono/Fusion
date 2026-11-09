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
from dataclasses import asdict
import sqlite3
from pathlib import Path

CAP_MICRO_USD = 2_000_000
CODING_CAP_MICRO_USD = 150_000
CODING_CALL_CAP = 4


class AggregateBudget:
    def __init__(self, path):
        self.path = str(Path(path).resolve())
        with self.connect() as db:
            db.executescript('''
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

    def reserve(self, stage, run, upper_micro):
        if stage not in ('planning', 'coding') or not isinstance(run, str) or not run:
            raise ValueError('invalid_reservation')
        if type(upper_micro) is not int or not 0 < upper_micro <= CAP_MICRO_USD:
            raise ValueError('invalid_upper_bound')
        # A separate connection per attempt is necessary for threads/processes.
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            total = db.execute('SELECT COALESCE(SUM(upper_micro),0) FROM reservations').fetchone()[0]
            used, calls = db.execute('SELECT COALESCE(SUM(upper_micro),0), COUNT(*) FROM reservations WHERE stage=? AND run=?', (stage, run)).fetchone()
            if total+upper_micro > CAP_MICRO_USD:
                raise ValueError('aggregate_spend_cap')
            if stage == 'coding' and (used+upper_micro > CODING_CAP_MICRO_USD or calls >= CODING_CALL_CAP):
                raise ValueError('coding_run_cap')
            ident = db.execute('INSERT INTO reservations(stage,run,upper_micro) VALUES (?,?,?)', (stage, run, upper_micro)).lastrowid
            db.execute('INSERT INTO transitions(reservation_id,state,basis) VALUES (?,?,?)',(ident,'RESERVED','worst_case'))
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


def guard_gateway(gateway, ledger, stage, run):
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
                reservation_id = ledger.reserve(stage, run, original.reserved-before)
                active.ident=reservation_id
                # Audit linking must also succeed before transport is permitted.
                gateway.artifacts.write(f'aggregate-reservation-{attempt:04}.json',
                    json.dumps({'reservation_id': reservation_id, 'stage': stage, 'run': run,
                                'policy_sha256':policy_hash, 'attempt': attempt, 'reserved_exposure_micro_usd': original.reserved-before},
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
            if status!=200 or not usage or length_truncated(response,content_type):
                ledger.transition(ident,'UNCERTAIN','missing_usage_or_incomplete_response')
            else:
                u=usage[-1]
                if any(type(u.get(k)) is not int or u[k]<0 for k in ('prompt_tokens','completion_tokens')):
                    ledger.transition(ident,'UNCERTAIN','invalid_usage')
                else:
                    estimate=(u['prompt_tokens']*gateway.policy.input_price_micro_per_million+u['completion_tokens']*gateway.policy.output_price_micro_per_million+999999)//1000000
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
