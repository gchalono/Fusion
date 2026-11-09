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
    shared_path=r/'shared-budget.db'
    current=(r/'test-double-experiment/experiment.db').exists()
    if current:shared_path=r/'test-double-experiment/experiment.db'
    if shared_path.exists():
        import sqlite3
        from decimal import Decimal,ROUND_CEILING
        with sqlite3.connect(f"file:{shared_path}?mode=ro",uri=True) as ledger_db:
            shared=ledger_db.execute("SELECT COALESCE(SUM(upper_micro),0),COUNT(*) FROM reservations WHERE stage='planning'").fetchone()
            assert shared[1]==v['gateway_forwarded_attempts']
            assert ledger_db.execute('SELECT COALESCE(SUM(upper_micro),0) FROM reservations').fetchone()[0]<=2000000
            expected=hashlib.sha256(canonical(read('gateway-policy.json'))).hexdigest()
            assert ledger_db.execute("SELECT policy_sha256 FROM run_policies WHERE stage='planning'").fetchone()[0]==expected
            if current:
                # FNXC:BlockerResolution 2026-11-09-18:27: Dynamic durable
                # exposure differs from the legacy fixed local audit bound.
                # Recheck every linked reservation and price/token upper bound.
                contract=json.loads(ledger_db.execute('SELECT body FROM experiment_contract WHERE id=1').fetchone()[0])
                for link_path in sorted(g.glob('aggregate-reservation-*.json')):
                    link=json.loads(link_path.read_text());ident=link['reservation_id']
                    amount=ledger_db.execute('SELECT upper_micro FROM reservations WHERE id=?',(ident,)).fetchone()[0]
                    bounds=ledger_db.execute('SELECT input_upper,output_upper FROM request_bounds WHERE reservation_id=?',(ident,)).fetchone()
                    body=json.loads((g/('request-'+link_path.stem.rsplit('-',1)[1]+'.json')).read_text())
                    assert amount==link['reserved_exposure_micro_usd']
                    assert len(canonical(body))<=bounds[0]<=contract['max_input_tokens']
                    assert body['max_tokens']<=bounds[1]<=contract['max_output_tokens']
                    minimum=int((Decimal(bounds[0])*Decimal(contract['input_usd_per_million'])+Decimal(bounds[1])*Decimal(contract['output_usd_per_million'])).to_integral_value(rounding=ROUND_CEILING))
                    assert amount>=minimum
                assert len(list(g.glob('aggregate-reservation-*.json')))==shared[1]
            else:assert shared[0]==total
            for ident,state in ledger_db.execute("SELECT r.id,(SELECT state FROM transitions t WHERE t.reservation_id=r.id ORDER BY t.id DESC LIMIT 1) FROM reservations r"):
                assert state in ('UNCERTAIN','SETTLED')
            assert ledger_db.execute('SELECT COUNT(*) FROM observations WHERE measured_charge_micro IS NOT NULL').fetchone()[0]==0

    if v['scenario'] == 'model-mismatch':
        assert v['native_failure'] and v['gateway_forwarded_attempts'] == 0
        assert 'model_mismatch' in v['gateway_blocked_reasons']
    else:
        assert not v['native_failure']
        native = read('native-test-double.json' if (r/'native-test-double.json').exists() else 'native-result.json')
        assert native['summary'] and native['classification'] in ('OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS','SYNTHETIC_OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS')
        if v['scenario'] == 'comprehensive':
            assert v['gateway_forwarded_attempts'] == 7
            if current:
                default=read('compaction.json');trigger=read('SYNTHETIC-triggered-compaction.json')
                assert default['reason']=='SESSION_TOO_SMALL' and default['settings']['keepRecentTokens']==20000
                assert trigger['classification']=='SYNTHETIC' and trigger['status']=='completed'
                assert trigger['settings']['keepRecentTokens']==512 and trigger['settings']['reserveTokens']<=4096
                approvals=read('approval-integration.json')
                assert approvals['classification']=='SYNTHETIC' and len(approvals['checks'])==7 and all(approvals['checks'].values())
                assert v['durable_count_match']
            else:assert read('compaction.json')['status']=='completed'
            assert [x['source'] for x in native['transcript']] == ['brief:storage', 'fixed-unknown']
            assert all(not json.loads(p.read_text())['usage_present'] for p in g.glob('result-*.json'))
    return {'classification': 'SYNTHETIC_OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS',
            'scenario': v['scenario'], 'verified': True, 'model_http_attempts': v['gateway_forwarded_attempts'],
            'database_changed_tables': db['changed_rows'], 'reserved_micro_usd_estimated': total}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('evidence_root')
    print(json.dumps(verify(parser.parse_args().evidence_root), indent=2))
