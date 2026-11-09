"""Durable conservative accounting, supplemental to Fusion's own limiter."""
import fcntl
import json
import time
from pathlib import Path
from gateway import Blocked, RATE_LIMIT_IDENTIFIER


def reserve_start(ledger, *, now=None, max_starts=5):
    # FNXC:NativeIsolation 2026-11-09-04:44: Apply stricter operator caps to the same ledger.
    if type(max_starts) is not int or not 1 <= max_starts <= 5:
        raise Blocked("invalid_native_start_cap")
    now = time.time() if now is None else now
    path = Path(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix + '.lock').open('a+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        text = path.read_text() if path.exists() else ''
        entries = json.loads(text) if text else []
        if any(e['identifier'] != RATE_LIMIT_IDENTIFIER for e in entries):
            raise Blocked('rate_limit_identifier_mismatch')
        active = [e for e in entries if now - e['timestamp'] < 3600]
        if len(active) >= max_starts:
            raise Blocked('native_start_self_limit')
        entries.append({'identifier': RATE_LIMIT_IDENTIFIER, 'timestamp': now})
        import os
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as pending:
            json.dump(entries, pending); pending.flush(); os.fsync(pending.fileno())
            pending_path = pending.name
        os.replace(pending_path, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
