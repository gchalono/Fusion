"""FNXC:Activation 2026-11-10-21:44: Non-consuming approval inspection only.
Reuse native signature, source and anchor checks; never authorize, reserve or dispatch.
"""
import argparse,contextlib,fcntl,json,math,os,sqlite3,time
from pathlib import Path
from history_budget import HistoryBudget,original_anchor,continuation_contract,sha,canonical,request_worst_case
from operator_auth import ApprovalVerifier,LIVE_TRUST,strict
import live_supervisor as supervisor

@contextlib.contextmanager
def readonly_ledger(path,witness):
    path,witness=Path(path),Path(witness)
    for p in (path,witness,Path(str(path)+'.owner')):
        if not p.is_file() or p.is_symlink():raise ValueError('original_ledger_witness_owner_required')
    owner=os.open(str(path)+'.owner',os.O_RDONLY);db=None
    try:
        fcntl.flock(owner,fcntl.LOCK_SH|fcntl.LOCK_NB)
        db=sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True)
        db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
        b=object.__new__(HistoryBudget);b.path=str(path);b.witness=witness;b._pid=os.getpid();b._owner=owner
        st=os.fstat(owner);b._owner_inode=(st.st_dev,st.st_ino);b.reader=original_anchor
        b.identity=json.loads(db.execute('SELECT body FROM continuation_identity WHERE id=1').fetchone()[0])
        b.contract=json.loads(db.execute('SELECT body FROM experiment_contract WHERE id=1').fetchone()[0])
        if b.identity['witness_path']!=str(witness.resolve()) or b.contract!=continuation_contract():raise ValueError('ledger_binding_mismatch')
        b._validate(db);yield b,db
    finally:
        if db is not None:db.close()
        os.close(owner)

def validate_scope(spec,b,db,*,now=None):
    now=time.time() if now is None else now
    required={'domain','model','arm','objective_sha256','seed_commit','source_commit','config_sha256','ledger_id','anchor_sha256','limits','nonce','expires_at','run_id'}
    limits={'requests':4,'input':32000,'output':4096,'run_seconds':300,'request_seconds':60,'run_micro_usd':120000,'aggregate_micro_usd':2000000}
    if set(spec)!=required or spec['limits']!=limits:raise ValueError('authorization_schema_or_limits')
    expected_domain='FUSION_PHASE3C_TEST' if b.identity['domain']=='TEST' else 'FUSION_PHASE3C_LIVE'
    if spec['domain']!=expected_domain or spec['model']!=supervisor.MODEL or spec['arm']!='A' or spec['run_id']!=supervisor.RUN:raise ValueError('model_arm_domain_or_run_mismatch')
    if type(spec['expires_at']) not in (int,float) or not math.isfinite(spec['expires_at']) or not 0<spec['expires_at']-now<=3600:raise ValueError('approval_expired_or_excessive_lifetime')
    if not isinstance(spec['nonce'],str) or len(spec['nonce'])!=64:raise ValueError('nonce_scope')
    if spec['ledger_id']!=b.identity['ledger_id'] or spec['anchor_sha256']!=b.identity['anchor_sha256'] or spec['config_sha256']!=sha(canonical(b.contract)):raise ValueError('approval_binding_mismatch')
    if spec['objective_sha256']!='4edc93814c7a6ad5c43445ad07f853ca3350ed0e3f6dc7764e1c04e0c4cdffe0' or spec['seed_commit']!='f2a49cb3fc7e02cd225053d4e2d07c589b4c808b':raise ValueError('task_or_seed_mismatch')
    if db.execute('SELECT 1 FROM run_authorizations').fetchone():raise ValueError('approval_consumed_or_other_run_authorized')
    if db.execute("SELECT 1 FROM run_controls WHERE status='ACTIVE'").fetchone():raise ValueError('another_run_active')
    if db.execute('SELECT 1 FROM reservations r LEFT JOIN continuation_settlements s ON s.reservation_id=r.id WHERE s.reservation_id IS NULL').fetchone():raise ValueError('outstanding_reservation_requires_operator_recovery')
    worst=4*request_worst_case(b.contract)
    anchor=b.reader();historical=anchor['historical_retained_micro_usd']+anchor['historical_unresolved_micro_usd']
    headroom=2000000-historical-500000-worst
    if worst>120000 or headroom<0:raise ValueError('budget_exceeded')
    return {'worst_case_micro_usd':worst,'headroom_after_run_micro_usd':headroom}

def check(approval,metadata):
    envelope=strict(Path(approval).read_bytes());v=ApprovalVerifier(LIVE_TRUST,envelope)
    spec=v.spec;supervisor.preflight(spec);supervisor.approved_metadata(metadata,envelope['payload'])
    if 'OPENAI_API_KEY' not in os.environ:raise ValueError('gateway_credential_not_configured')
    p,w=supervisor.state_paths()
    with readonly_ledger(p,w) as (b,db):
        if b.identity['domain']!='LIVE':raise ValueError('live_ledger_required')
        budget=validate_scope(spec,b,db)
    return {'status':'PREFLIGHT_PASSED_NOT_AUTHORIZED_OR_CONSUMED',**budget,'nonce_consumed':False,'reservations_created':0,'inference_requests':0,'credential_value_read':False,'recheck_at_execution_required':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--approval',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);a=p.parse_args()
    try:print(json.dumps(check(a.approval,a.metadata)))
    except Exception as e:
        print(json.dumps({'status':'PREFLIGHT_BLOCKED','code':str(e) if isinstance(e,ValueError) else type(e).__name__,'inference_requests':0}));raise SystemExit(3)
if __name__=='__main__':main()
