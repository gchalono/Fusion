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
        # Return only AFTER commit. Failed/uncertain commits never reach transport.
        return ident

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
        exposure = sum(r['reserved_exposure_micro_usd'] for r in rows)
        return {'cap_micro_usd': CAP_MICRO_USD, 'reserved_exposure_micro_usd': exposure,
                'remaining_reservable_micro_usd': CAP_MICRO_USD-exposure,
                'reservations': rows, 'observations': observations}


def guard_gateway(gateway, ledger, stage, run):
    """Offline integration with the existing gateway; no new supervisor."""
    original = gateway.budget
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
                # Audit linking must also succeed before transport is permitted.
                gateway.artifacts.write(f'aggregate-reservation-{attempt:04}.json',
                    json.dumps({'reservation_id': reservation_id, 'stage': stage, 'run': run,
                                'attempt': attempt, 'reserved_exposure_micro_usd': original.reserved-before},
                               sort_keys=True).encode())
                return attempt
            except BaseException:
                original.failed = True
                raise
    gateway.budget = Guard()
    return gateway
