"""FNXC:BlockerResolution 2026-11-09-18:27:
SYNTHETIC reproducibility checks for two identical Arm A profiles. Optionally
continue an existing native fixture experiment to verify planning and actual
coding attempts share its durable ledger. Never loads a provider credential.
"""
import argparse
import hashlib
import json
from pathlib import Path
from budget import AggregateBudget
from contract import canonical
from independent import evaluate_patch
from offline_eval import start_stub
from pilot import initialize,execute_agent,fixture_binding


def run(root,runtime,existing=False):
    if not existing:initialize(root)
    server,contacts=start_stub(root)
    try:
        report,candidate,_=execute_agent(root,runtime,'merge-intervals:A')
        grade=evaluate_patch('merge-intervals',(root/'candidate.patch').read_text(),root/'SYNTHETIC-independent-check')
        assert report['exit_code']==0 and not report['timed_out'] and grade['success']
        ledger=AggregateBudget(root/'experiment.db').snapshot()
        rows=[r for r in ledger['reservations'] if r['stage']=='coding'];ids={r['id']:i for i,r in enumerate(rows)}
        normalized={'classification':'SYNTHETIC','candidate_sha256':hashlib.sha256(candidate).hexdigest(),'patch':(root/'candidate.patch').read_text(),'grading':{k:grade[k] for k in ('tests','passed','failed','errors','success')},'contacts':contacts,'reservations_micro_usd':[r['reserved_exposure_micro_usd'] for r in rows],'observations':[{k:v for k,v in o.items() if k not in ('id','reservation_id','evidence_ref')} for o in ledger['observations'] if o['reservation_id'] in ids],'transitions':[(ids[t['reservation_id']],t['state'],t['basis']) for t in ledger['transitions'] if t['reservation_id'] in ids]}
        (root/'SYNTHETIC-normalized.json').write_bytes(canonical(normalized))
        (root/'SYNTHETIC-final-ledger.json').write_bytes(canonical(ledger))
        if existing:
            assert {r['stage'] for r in ledger['reservations']}=={'planning','coding'}
            assert ledger['reserved_exposure_micro_usd']<=2000000
        return normalized,ledger
    finally:server.shutdown();server.server_close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--existing-experiment',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    print(json.dumps({'classification':'SYNTHETIC','fixture':fixture_binding()}),flush=True)
    first=a.existing_experiment or a.output/'SYNTHETIC-A1';one,ledger=run(first,a.runtime,existing=bool(a.existing_experiment));two,_=run(a.output/'SYNTHETIC-A2',a.runtime)
    assert one==two,'SYNTHETIC_normalized_reproducibility_mismatch'
    result={'classification':'SYNTHETIC','identical_normalized_profiles':True,'normalized_sha256':hashlib.sha256(canonical(one)).hexdigest(),'compared':['patch','grading','request_accounting','coding_ledger_reservations_usage_estimates_transitions'],'shared_planning_coding_ledger':bool(a.existing_experiment),'shared_exposure_micro_usd':ledger['reserved_exposure_micro_usd'],'coding_attempts':len(one['contacts']),'fixture':fixture_binding()}
    (a.output/'SYNTHETIC-reproducibility.json').write_bytes(canonical(result));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
