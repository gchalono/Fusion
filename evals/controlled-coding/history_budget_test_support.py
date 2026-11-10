"""FNXC:HistoricalLedger 2026-11-10-05:38: Explicit TEST-domain synthetic
47-record fixture and signing; never a live key/approval or genuine evidence.
"""
import hashlib,hmac,json,os,secrets,subprocess,time
from pathlib import Path
from contract import canonical
from history_budget import HistoryBudget,sha
KEY=b'LOCAL_TEST_DOMAIN_KEY_NOT_PROVIDER_OR_OPERATOR'
class Reader:
 def __init__(self,path,unresolved=0):self.path=Path(path);self.unresolved=unresolved
 def __call__(self):
  records=[{'name':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(self.path.iterdir())]
  return {'schema_version':1,'journal_id':'SYNTHETIC:47-records','journal_sha256':sha(canonical(records)),'journal_bytes':sum(x['bytes'] for x in records),'record_count':len(records),'historical_retained_micro_usd':11522,'historical_unresolved_micro_usd':self.unresolved,'historical_planning_micro_usd':11522,'records':records}
def fixture(root,unresolved=0):
 root=Path(root);j=root/'synthetic-journal';j.mkdir()
 for i in range(47):(j/f'{i:02}.json').write_bytes(canonical({'classification':'SYNTHETIC','record':i}))
 r=Reader(j,unresolved);p=root/'continuation.db';w=root/'witness.json';HistoryBudget.initialize(p,w,reader=r,test_key=KEY);return p,w,r

def spec(b):
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[2],text=True).strip()
 return {'domain':'FUSION_PHASE3C_TEST','model':b.contract['model'],'arm':'A','objective_sha256':'4edc93814c7a6ad5c43445ad07f853ca3350ed0e3f6dc7764e1c04e0c4cdffe0','seed_commit':'f2a49cb3fc7e02cd225053d4e2d07c589b4c808b','source_commit':head,'config_sha256':sha(canonical(b.contract)),'ledger_id':b.identity['ledger_id'],'anchor_sha256':b.identity['anchor_sha256'],'limits':{'requests':4,'input':32000,'output':4096,'run_seconds':300,'request_seconds':60,'run_micro_usd':120000,'aggregate_micro_usd':2000000},'nonce':secrets.token_hex(32),'expires_at':time.time()+900,'run_id':b.contract['coding_run_ids'][0]}
def sign(s):return hmac.new(KEY,canonical(s),'sha256').hexdigest()
def open_(p,w,r,**kw):return HistoryBudget(p,w,reader=r,test_key=KEY,**kw)
def start(p,w,r,**kw):
 b=open_(p,w,r,**kw);s=spec(b);b.authorize_run(s,sign(s));return b,s['run_id']
def reserve(b,run):return b.reserve('coding',run,19354,token_bounds=(32000,4096))
