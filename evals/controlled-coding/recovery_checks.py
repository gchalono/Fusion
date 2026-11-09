"""FNXC:OfflineFinal 2026-11-09-06:35:
Owned-process interruption/abort checks against local TLS only. No native starts,
no provider traffic, and every resumed attempt uses the original durable ledger.
"""
import argparse
import json
from pathlib import Path
import threading
import time
from budget import AggregateBudget
from contract import canonical
from offline_eval import start_stub
from pilot import initialize,execute_agent,spawn_broker,request_admin


def check(root,runtime,action):
    initialize(root);contact=threading.Event();release=threading.Event();owned=threading.Event();holder={};out={}
    server,contacts=start_stub(root,pause=(contact,release))
    run='merge-intervals:A'
    def hook(process):holder['process']=process;owned.set()
    def execute():
        try:out['value']=execute_agent(root,runtime,run,broker_hook=hook)
        except Exception as error:out['error']=type(error).__name__+':'+str(error)
    thread=threading.Thread(target=execute);thread.start()
    try:
        assert owned.wait(10) and contact.wait(20),'request_not_forwarded'
        token=(root/'local-token').read_bytes()
        before=AggregateBudget(root/'experiment.db').snapshot()
        if action=='kill':holder['process'].kill()
        else:assert request_admin(root,'abort')['ok']
        release.set();thread.join(20)
        assert not thread.is_alive() and 'error' not in out,out
        assert out['value'][0]['aborted'],out['value'][0]
        ledger=AggregateBudget(root/'experiment.db');after=ledger.snapshot()
        assert after['reserved_exposure_micro_usd']==before['reserved_exposure_micro_usd']>0
        with ledger.connect() as db:
            states=[r[0] for r in db.execute('SELECT state FROM transitions t WHERE id=(SELECT MAX(id) FROM transitions WHERE reservation_id=t.reservation_id)')]
            control=db.execute('SELECT status FROM run_controls').fetchone()[0]
        assert 'UNCERTAIN' in states and control=='INCOMPLETE',(states,control)
        try:spawn_broker(root,run)
        except RuntimeError:pass
        else:raise AssertionError('implicit_resume_allowed')
        resumed=execute_agent(root,runtime,run,resume=True)
        assert resumed[0]['exit_code']==0
        assert token!=(root/'local-token').read_bytes(),'token_not_rotated'
        final=ledger.snapshot()
        with ledger.connect() as db:
            states=[r[0] for r in db.execute('SELECT state FROM transitions t WHERE id=(SELECT MAX(id) FROM transitions WHERE reservation_id=t.reservation_id) ORDER BY reservation_id')]
            attempts=db.execute('SELECT COUNT(*) FROM reservations').fetchone()[0]
        assert attempts==4 and len(contacts)==4,(attempts,len(contacts))
        assert 'UNCERTAIN' in states and final['reserved_exposure_micro_usd']>after['reserved_exposure_micro_usd']
        record={'classification':'OFFLINE_RECOVERY_TEST_DOUBLE','action':action,'uncertain_exposure_preserved':True,'default_restart_refused':True,'explicit_resume_succeeded':True,'local_token_rotated':True,'attempts':attempts,'contacts':len(contacts),'states':states,'ledger':final}
        (root/'recovery-observation.json').write_bytes(canonical(record))
        return record
    finally:
        release.set();server.shutdown();server.server_close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    records=[check(a.output/action,a.runtime,action) for action in ('kill','abort')]
    print(json.dumps(records,indent=2))
if __name__=='__main__':main()
