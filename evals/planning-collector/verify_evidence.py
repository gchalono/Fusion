"""Recheck already captured OFFLINE evidence; never starts an interview."""
import argparse
import hashlib
import json
from pathlib import Path
from gateway import canonical
from snapshots import database_diff, filesystem_diff, process_diff


def verify(root):
    root = Path(root)
    if not (root / '.offline-test').is_file(): raise ValueError('not_offline_evidence')
    r = root / 'results'
    read = lambda n: json.loads((r/n).read_text())
    v = read('verification.json')
    db = database_diff(read('database-before.json'), read('database-after.json'))
    fs = filesystem_diff(read('filesystem-before.json'), read('filesystem-after.json'))
    processes = process_diff(read('processes-before.json'), read('processes-after.json'))
    assert not db['forbidden'] and not fs['unexpected'] and not processes['unexpected']
    assert v['request_count_match'] and v['direct_mock_bypass_blocked'] and v['external_route_blocked']
    assert read('mcp.json') == {'servers': [], 'errors': []}
    g = root / 'scratch' / 'gateway-artifacts'
    total = 0
    for p in sorted(g.glob('reservation-*.json')):
        n = p.stem.split('-')[1]
        reservation = json.loads(p.read_text())
        body = json.loads((g/f'request-{n}.json').read_text())
        assert reservation['request_sha256'] == hashlib.sha256(canonical(body)).hexdigest(), 'request_was_modified'
        record = json.loads((g/f'result-{n}.json').read_text())
        for key in ('request', 'response'):
            artifact = record[key]
            assert hashlib.sha256((g/artifact['file']).read_bytes()).hexdigest() == artifact['sha256']
        assert record['output_limit_intervention'] is False
        total += reservation['reserved_micro_usd']
    assert total == v['reserved_micro_usd_estimated']
    if (r/'shared-budget.db').exists():
        import sqlite3
        with sqlite3.connect(f"file:{r/'shared-budget.db'}?mode=ro",uri=True) as db:
            shared=db.execute('SELECT COALESCE(SUM(upper_micro),0),COUNT(*) FROM reservations').fetchone()
            assert shared[0]==total and shared[1]==v['gateway_forwarded_attempts']
            assert shared[0]<=2000000
            expected=hashlib.sha256(canonical(read('gateway-policy.json'))).hexdigest()
            assert db.execute('SELECT policy_sha256 FROM run_policies').fetchone()[0]==expected
            for ident,state in db.execute("SELECT r.id,(SELECT state FROM transitions t WHERE t.reservation_id=r.id ORDER BY t.id DESC LIMIT 1) FROM reservations r"):
                assert state in ('UNCERTAIN','SETTLED')
            assert db.execute('SELECT COUNT(*) FROM observations WHERE measured_charge_micro IS NOT NULL').fetchone()[0]==0

    if v['scenario'] == 'model-mismatch':
        assert v['native_failure'] and v['gateway_forwarded_attempts'] == 0
        assert 'model_mismatch' in v['gateway_blocked_reasons']
    else:
        assert not v['native_failure']
        native = read('native-test-double.json' if (r/'native-test-double.json').exists() else 'native-result.json')
        assert native['summary'] and native['classification'] == 'OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS'
        if v['scenario'] == 'comprehensive':
            assert v['gateway_forwarded_attempts'] == 7
            assert read('compaction.json')['status'] == 'completed'
            assert [x['source'] for x in native['transcript']] == ['brief:storage', 'fixed-unknown']
            assert all(not json.loads(p.read_text())['usage_present'] for p in g.glob('result-*.json'))
    return {'classification': 'OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS',
            'scenario': v['scenario'], 'verified': True, 'model_http_attempts': v['gateway_forwarded_attempts'],
            'database_changed_tables': db['changed_rows'], 'reserved_micro_usd_estimated': total}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('evidence_root')
    print(json.dumps(verify(parser.parse_args().evidence_root), indent=2))
