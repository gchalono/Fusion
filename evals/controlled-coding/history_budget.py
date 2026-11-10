"""FNXC:HistoricalLedger 2026-11-10-05:38: Continuation adapter for the existing
AggregateBudget/gateway admission interface. Original journal is READ ONLY.
Operator signatures are external; only TEST-domain HMAC is mintable in dev tests.
"""
import contextlib,fcntl,hashlib,hmac,json,os,secrets,signal,sqlite3,subprocess,sys,threading,time
from pathlib import Path
from budget import AggregateBudget
from contract import canonical
ROOT=Path(__file__).resolve().parent
ZERO='0'*64

def sha(raw):return hashlib.sha256(raw).hexdigest()
def original_anchor():
 p=subprocess.run([sys.executable,'-B',str(ROOT/'journal_replay.py')],env={'PATH':os.defpath,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,timeout=30)
 if p.returncode:raise ValueError('historical_replay_failed; inspect read-only replay receipt')
 return json.loads(p.stdout)

def request_worst_case(contract):
 from decimal import Decimal,ROUND_CEILING
 return int((Decimal(contract['max_input_tokens'])*Decimal(contract['input_usd_per_million'])+Decimal(contract['max_output_tokens'])*Decimal(contract['output_usd_per_million'])).to_integral_value(rounding=ROUND_CEILING))

def continuation_contract():
 from task_manager_adapter import experiment_contract
 d=experiment_contract();d['frozen_coding_token_limit']=144384
 return d

class HistoryBudget(AggregateBudget):
 @classmethod
 def initialize(cls,path,witness,*,reader=None,test_key=None):
  path,witness=Path(path),Path(witness)
  if path.exists() or witness.exists():raise ValueError('continuation_or_witness_already_exists; never reset')
  if reader is not None and test_key is None:raise ValueError('test_reader_requires_test_domain')
  anchor=(reader or original_anchor)();cls._check_anchor(anchor)
  path.parent.mkdir(parents=True,exist_ok=True);path.parent.chmod(0o700)
  # An exclusive initializer claim persists even if bootstrap crashes.
  claim=path.with_suffix(path.suffix+'.initialized')
  try:fd=os.open(claim,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  except FileExistsError:raise ValueError('initialization_already_claimed; restore original continuation') from None
  os.close(fd)
  base=AggregateBudget(path,experiment_contract=continuation_contract());path.chmod(0o600)
  with base.connect() as db:
   db.execute('PRAGMA journal_mode=WAL')
   db.executescript('''
    CREATE TABLE history_anchor (id INTEGER PRIMARY KEY CHECK(id=1),body TEXT NOT NULL);
    CREATE TABLE continuation_identity (id INTEGER PRIMARY KEY CHECK(id=1),body TEXT NOT NULL);
    CREATE TABLE continuation_events (seq INTEGER PRIMARY KEY,body TEXT NOT NULL,previous TEXT NOT NULL,hash TEXT NOT NULL);
    CREATE TABLE continuation_settlements (reservation_id INTEGER PRIMARY KEY REFERENCES reservations(id),charge INTEGER NOT NULL CHECK(charge>=0),state TEXT NOT NULL);
    CREATE TABLE run_authorizations (run TEXT PRIMARY KEY,body TEXT NOT NULL,signature TEXT NOT NULL);
   ''')
   for table in ('history_anchor','continuation_identity','continuation_events','continuation_settlements','run_authorizations'):
    for op in ('UPDATE','DELETE'):db.execute(f"CREATE TRIGGER {table}_no_{op.lower()} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'immutable_{table}'); END;")
   for table,key in [('history_anchor','id'),('continuation_identity','id'),('continuation_events','seq'),('continuation_settlements','reservation_id'),('run_authorizations','run')]:
    db.execute(f"CREATE TRIGGER {table}_no_replace BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {table} WHERE {key}=NEW.{key}) BEGIN SELECT RAISE(ABORT,'immutable_{table}'); END;")
   db.execute('INSERT INTO history_anchor VALUES (1,?)',(canonical(anchor).decode(),))
   identity={'schema_version':1,'ledger_id':secrets.token_hex(32),'anchor_sha256':sha(canonical(anchor)),'domain':'TEST' if test_key is not None else 'LIVE','witness_path':str(witness.resolve())}
   db.execute('INSERT INTO continuation_identity VALUES (1,?)',(canonical(identity).decode(),))
   cls._chain(db,'BOOTSTRAP')
  obj=object.__new__(cls);obj.path=str(path.resolve());obj.witness=witness;obj.identity=identity
  obj._write_witness()
  return identity

 @staticmethod
 def _check_anchor(a):
  for k in ('journal_sha256','journal_id','schema_version','journal_bytes','record_count','historical_retained_micro_usd','historical_unresolved_micro_usd','historical_planning_micro_usd','records'):
   if k not in a:raise ValueError('anchor_missing_field')
  if a['schema_version']!=1 or a['record_count']!=47 or len(a['records'])!=47:raise ValueError('anchor_schema_or_count')
  for k in ('journal_bytes','historical_retained_micro_usd','historical_unresolved_micro_usd','historical_planning_micro_usd'):
   if type(a[k]) is not int or a[k]<0:raise ValueError('ambiguous_historical_amount')

 def __init__(self,path,witness,*,reader=None,test_key=None,recover=False,crash_at=None,operator_verifier=None):
  self.path=str(Path(path).resolve());self.witness=Path(witness).resolve();self.reader=reader or original_anchor;self.test_key=test_key;self.operator_verifier=operator_verifier
  self.crash_at=crash_at;self._mutex=threading.RLock();self._pid=os.getpid();self._owner=None
  if reader is not None and test_key is None:raise ValueError('test_reader_requires_test_domain')
  if crash_at and test_key is None:raise ValueError('crash_injection_test_only')
  if not Path(self.path).is_file() or Path(self.path).is_symlink() or Path(self.path).stat().st_size==0 or not self.witness.is_file() or self.witness.is_symlink():raise ValueError('anchored_continuation_and_witness_required; do not initialize a replacement')
  self._owner=os.open(self.path+'.owner',os.O_RDWR|os.O_CREAT,0o600)
  try:
   fcntl.flock(self._owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
   st=os.fstat(self._owner);self._owner_inode=(st.st_dev,st.st_ino)
   with self.connect() as db:
    db.execute('BEGIN IMMEDIATE')
    self.identity=json.loads(db.execute('SELECT body FROM continuation_identity WHERE id=1').fetchone()[0]);self.anchor=json.loads(db.execute('SELECT body FROM history_anchor WHERE id=1').fetchone()[0]);self.contract=json.loads(db.execute('SELECT body FROM experiment_contract WHERE id=1').fetchone()[0])
    if self.identity['witness_path']!=str(self.witness) or (self.test_key is not None)!=(self.identity['domain']=='TEST'):raise ValueError('ledger_identity_or_domain_mismatch')
    if self.contract!=continuation_contract():raise ValueError('continuation_contract_mismatch')
    self._validate(db,allow_ancestor=recover)
    active=db.execute("SELECT COUNT(*) FROM run_controls WHERE status='ACTIVE'").fetchone()[0]
    outstanding=db.execute('SELECT COUNT(*) FROM reservations r LEFT JOIN continuation_settlements s ON s.reservation_id=r.id WHERE s.reservation_id IS NULL').fetchone()[0]
    if active or outstanding:
     if not recover:raise ValueError('crashed_run_requires_explicit_recovery; never resume/replay')
     self._recover_rows(db);self._chain(db,'RECOVERY_RETAIN_AND_TERMINALIZE')
    elif recover:self._chain(db,'EXPLICIT_RECOVERY_VALIDATED')
   if recover:self._write_witness()
  except BaseException:
   self._unlock();raise

 def connect(self):
  db=sqlite3.connect('file:'+self.path+'?mode=rw',uri=True,timeout=10)
  db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA synchronous=FULL')
  if db.execute('PRAGMA journal_mode').fetchone()[0].lower()!='wal':db.close();raise ValueError('WAL_required')
  return db

 @staticmethod
 def _state(db):
  names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name") if r[0]!='continuation_events']
  state={n:db.execute('SELECT * FROM "'+n+'" ORDER BY rowid').fetchall() for n in names}
  state['_schema']=db.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
  return sha(canonical(state))

 @classmethod
 def _chain(cls,db,kind):
  old=db.execute('SELECT seq,hash FROM continuation_events ORDER BY seq DESC LIMIT 1').fetchone();seq=old[0]+1 if old else 1;prev=old[1] if old else ZERO
  body=canonical({'kind':kind,'state_sha256':cls._state(db)}).decode();head=sha(canonical([seq,prev,body]));db.execute('INSERT INTO continuation_events VALUES (?,?,?,?)',(seq,body,prev,head))

 def _validate(self,db,*,allow_ancestor=False):
  if os.getpid()!=self._pid or self._owner is None:raise ValueError('gateway_owner_required')
  st=os.stat(self.path+'.owner')
  if (st.st_dev,st.st_ino)!=self._owner_inode:raise ValueError('owner_lock_replaced')
  actual=self.reader();self._check_anchor(actual)
  stored=json.loads(db.execute('SELECT body FROM history_anchor WHERE id=1').fetchone()[0])
  if stored!=actual or sha(canonical(stored))!=self.identity['anchor_sha256']:raise ValueError('original_anchor_mismatch; no automatic repair')
  if json.loads(db.execute('SELECT body FROM continuation_identity WHERE id=1').fetchone()[0])!=self.identity:raise ValueError('continuation_identity_changed')
  if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('continuation_corrupt')
  prev=ZERO;rows=db.execute('SELECT seq,body,previous,hash FROM continuation_events ORDER BY seq').fetchall()
  for i,(seq,body,p,h) in enumerate(rows,1):
   if seq!=i or p!=prev or h!=sha(canonical([seq,p,body])):raise ValueError('continuation_hash_chain_invalid')
   prev=h
  if not rows or json.loads(rows[-1][1])['state_sha256']!=self._state(db):raise ValueError('continuation_state_changed')
  w=json.loads(self.witness.read_bytes())
  if any(w.get(k)!=self.identity[k] for k in ('ledger_id','anchor_sha256')):raise ValueError('witness_identity_mismatch')
  seq=w.get('seq')
  if type(seq) is not int or seq<1 or seq>len(rows) or rows[seq-1][3]!=w.get('head'):raise ValueError('witness_ahead_or_mismatch; refuse dispatch')
  if seq!=len(rows) and not allow_ancestor:raise ValueError('continuation_ahead_of_witness; explicit recovery required')

 def _write_witness(self):
  with self.connect() as db:seq,head=db.execute('SELECT seq,hash FROM continuation_events ORDER BY seq DESC LIMIT 1').fetchone()
  w={k:self.identity[k] for k in ('ledger_id','anchor_sha256')};w.update(seq=seq,head=head)
  tmp=self.witness.with_name(self.witness.name+'.'+secrets.token_hex(8)+'.tmp')
  fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as f:f.write(canonical(w));f.flush();os.fsync(f.fileno())
  os.replace(tmp,self.witness);fd=os.open(self.witness.parent,os.O_DIRECTORY)
  try:os.fsync(fd)
  finally:os.close(fd)

 def _mutate(self,kind,fn):
  with self._mutex:
   with self.connect() as db:
    db.execute('BEGIN IMMEDIATE');self._validate(db);value=fn(db);self._chain(db,kind)
   self._crash('after_'+kind.lower()+'_commit');self._write_witness();return value

 def _crash(self,point):
  if self.crash_at==point:
   print('INJECTION:'+point,flush=True);os.kill(os.getpid(),signal.SIGKILL)

 def _exposure(self,db,stage=None,run=None):
  where='';params=[]
  if stage is not None:where=' WHERE r.stage=?';params.append(stage)
  if run is not None:where+=' AND r.run=?';params.append(run)
  amount=db.execute('SELECT COALESCE(SUM(COALESCE(s.charge,r.upper_micro)),0) FROM reservations r LEFT JOIN continuation_settlements s ON s.reservation_id=r.id'+where,params).fetchone()[0]
  if run is None and stage in (None,'planning'):amount+=self.anchor['historical_retained_micro_usd']+self.anchor['historical_unresolved_micro_usd']
  return amount

 def _auth(self,db,run):
  row=db.execute('SELECT body,signature FROM run_authorizations WHERE run=?',(run,)).fetchone()
  if not row:raise ValueError('operator_signed_authorization_required')
  spec=json.loads(row[0]);sig=row[1]
  if self.identity['domain']=='LIVE' and spec.get('domain')!='FUSION_PHASE3C_LIVE':raise ValueError('test_domain_unavailable_live')
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parents[1],text=True).strip()
  if spec['source_commit']!=head:raise ValueError('authorization_source_mismatch')
  if self.identity['domain']=='LIVE' and subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT.parents[1],text=True).strip():raise ValueError('live_source_dirty')
  if (spec['ledger_id']!=self.identity['ledger_id'] or spec['anchor_sha256']!=self.identity['anchor_sha256'] or spec['config_sha256']!=sha(canonical(self.contract)) or time.time()>=spec['expires_at']):raise ValueError('authorization_stale_or_binding_mismatch')
  if self.identity['domain']=='TEST':
   if spec['domain']!='FUSION_PHASE3C_TEST' or self.test_key is None or not hmac.compare_digest(sig,hmac.new(self.test_key,canonical(spec),'sha256').hexdigest()):raise ValueError('test_signature_invalid')
  elif spec['domain']!='FUSION_PHASE3C_LIVE' or self.operator_verifier is None or self.operator_verifier(spec,sig) is not True:raise ValueError('operator_signing_trust_not_configured')
  return spec

 def authorize_run(self,spec,signature):
  def insert(db):
   if not isinstance(signature,str) or not signature.isascii() or not 0<len(signature)<=1024:raise ValueError('signature_encoding')
   required={'domain','model','arm','objective_sha256','seed_commit','source_commit','config_sha256','ledger_id','anchor_sha256','limits','nonce','expires_at','run_id'}
   if set(spec)!=required:raise ValueError('authorization_schema')
   limits={'requests':4,'input':32000,'output':4096,'run_seconds':300,'request_seconds':60,'run_micro_usd':120000,'aggregate_micro_usd':2000000}
   if spec['limits']!=limits or spec['model']!=self.contract['model'] or spec['arm']!='A' or spec['run_id']!=self.contract['coding_run_ids'][0] or not isinstance(spec['nonce'],str) or len(spec['nonce'])!=64 or not 0<spec['expires_at']-time.time()<=3600:raise ValueError('authorization_limits_or_scope')
   if spec['objective_sha256']!='4edc93814c7a6ad5c43445ad07f853ca3350ed0e3f6dc7764e1c04e0c4cdffe0' or spec['seed_commit']!='f2a49cb3fc7e02cd225053d4e2d07c589b4c808b':raise ValueError('authorization_task_mismatch')
   if db.execute("SELECT 1 FROM run_controls WHERE status='ACTIVE'").fetchone():raise ValueError('another_run_active')
   if db.execute('SELECT 1 FROM run_authorizations').fetchone():raise ValueError('one_authorized_run_only; no automatic successor')
   db.execute('INSERT INTO run_authorizations VALUES (?,?,?)',(spec['run_id'],canonical(spec).decode(),signature));self._auth(db,spec['run_id'])
   now=time.time();db.execute('INSERT INTO run_controls VALUES (?,?,?,?,?)',('coding',spec['run_id'],now,min(now+300,spec['expires_at']),'ACTIVE'))
  self._mutate('AUTHORIZE',insert)

 def control_run(self,stage,run,action):
  if stage!='coding' or action not in ('COMPLETE','INCOMPLETE'):raise ValueError('start_requires_signed_authorization; resume_forbidden')
  def update(db):
   if not db.execute('SELECT 1 FROM run_controls WHERE stage=? AND run=?',(stage,run)).fetchone():raise ValueError('unknown_run')
   db.execute('UPDATE run_controls SET status=? WHERE stage=? AND run=?',(action,stage,run))
  self._mutate('TERMINALIZE',update)

 def bind_policy(self,stage,run,policy_hash):
  def bind(db):
   self._auth(db,run);old=db.execute('SELECT policy_sha256 FROM run_policies WHERE stage=? AND run=?',(stage,run)).fetchone()
   if stage!='coding' or len(policy_hash)!=64 or (old and old[0]!=policy_hash):raise ValueError('run_policy_mismatch')
   if not old:db.execute('INSERT INTO run_policies VALUES (?,?,?)',(stage,run,policy_hash))
  self._mutate('POLICY',bind)

 def _before_reservation(self,db,stage,run,amount,bounds):
  self._validate(db);self._auth(db,run)
  if stage!='coding' or bounds!=(32000,4096) or amount!=request_worst_case(self.contract):raise ValueError('fixed_uncached_request_reservation_required')
 def _after_reservation(self,db,ident):self._chain(db,'RESERVE')
 def _reservation_persisted(self):self._crash('after_reserve_commit');self._write_witness();self._crash('before_dispatch')
 def reserve(self,*a,**kw):
  with self._mutex:return super().reserve(*a,**kw)

 def observe(self,reservation_id,*,evidence_ref,provider_usage=None,estimated_charge_micro=None,measured_charge_micro=None):
  if measured_charge_micro is not None:raise ValueError('provider_usage_is_not_invoice')
  def add(db):
   if not isinstance(evidence_ref,str) or not evidence_ref:raise ValueError('evidence_required')
   db.execute('INSERT INTO observations(reservation_id,provider_usage_json,estimated_charge_micro,measured_charge_micro,evidence_ref) VALUES (?,?,?,?,?)',(reservation_id,json.dumps(provider_usage,allow_nan=False),estimated_charge_micro,None,evidence_ref))
  self._mutate('OBSERVE',add)

 def _settle_row(self,db,ident,state,basis):
  row=db.execute('SELECT upper_micro FROM reservations WHERE id=?',(ident,)).fetchone()
  if not row:raise ValueError('unknown_reservation')
  charge=row[0]
  if state=='SETTLED':
   obs=db.execute('SELECT provider_usage_json FROM observations WHERE reservation_id=? ORDER BY id DESC LIMIT 1',(ident,)).fetchone()
   try:
    u=json.loads(obs[0]);i,o=u['prompt_tokens'],u['completion_tokens']
    if set(u)-{'prompt_tokens','completion_tokens','total_tokens','prompt_tokens_details','completion_tokens_details'}:raise ValueError()
    for name,key,upper in [('prompt_tokens_details','cached_tokens',i),('completion_tokens_details','reasoning_tokens',o)]:
     detail=u.get(name,{})
     if not isinstance(detail,dict) or set(detail)-{key} or type(detail.get(key,0)) is not int or not 0<=detail.get(key,0)<=upper:raise ValueError()
    if type(i) is not int or type(o) is not int or not 0<i<=32000 or not 0<=o<=4096 or ('total_tokens' in u and u['total_tokens']!=i+o):raise ValueError()
    charge=(i*400000+o*1600000+999999)//1000000
    if charge>row[0]:raise ValueError()
   except (TypeError,ValueError,KeyError):state='UNCERTAIN';charge=row[0]
  db.execute('INSERT INTO continuation_settlements VALUES (?,?,?)',(ident,charge,state))
  db.execute('INSERT INTO transitions(reservation_id,state,basis) VALUES (?,?,?)',(ident,state,basis))

 def transition(self,ident,state,basis):
  def change(db):
   old=db.execute('SELECT state FROM transitions WHERE reservation_id=? ORDER BY id DESC LIMIT 1',(ident,)).fetchone()
   if not old or state not in {'RESERVED':{'FORWARDED','UNCERTAIN'},'FORWARDED':{'SETTLED','UNCERTAIN'}}.get(old[0],set()):raise ValueError('invalid_ledger_transition')
   if state=='FORWARDED':db.execute('INSERT INTO transitions(reservation_id,state,basis) VALUES (?,?,?)',(ident,state,basis))
   else:self._settle_row(db,ident,state,basis)
  self._mutate('SETTLE' if state!='FORWARDED' else 'FORWARD',change)
  if state=='FORWARDED':self._crash('after_forward_commit')

 def _recover_rows(self,db):
  ids=[r[0] for r in db.execute('SELECT r.id FROM reservations r LEFT JOIN continuation_settlements s ON s.reservation_id=r.id WHERE s.reservation_id IS NULL')]
  for ident in ids:self._settle_row(db,ident,'UNCERTAIN','explicit_recovery_full_reservation')
  db.execute("UPDATE run_controls SET status='INCOMPLETE' WHERE status='ACTIVE'")
  return len(ids)
 def recover_uncertain(self):return self._mutate('RECOVERY',self._recover_rows)

 def snapshot(self):
  with self._mutex,self.connect() as db:
   db.execute('BEGIN');self._validate(db);exposure=self._exposure(db)
   rows=db.execute('SELECT id,stage,run,upper_micro FROM reservations ORDER BY id').fetchall();settlements=db.execute('SELECT * FROM continuation_settlements ORDER BY reservation_id').fetchall()
   return {'ledger_id':self.identity['ledger_id'],'anchor_sha256':self.identity['anchor_sha256'],'exposure_micro_usd':exposure,'remaining_micro_usd':2000000-exposure,'historical_retained_micro_usd':self.anchor['historical_retained_micro_usd'],'historical_unresolved_micro_usd':self.anchor['historical_unresolved_micro_usd'],'requests':len(rows),'reservations':rows,'settlements':settlements,'runs':db.execute('SELECT * FROM run_controls ORDER BY stage,run').fetchall()}

 def _unlock(self):
  if self._owner is not None:os.close(self._owner);self._owner=None
 def close(self):
  try:
   if self._owner is not None:
    with self.connect() as db:active=db.execute("SELECT 1 FROM run_controls WHERE status='ACTIVE'").fetchone()
    if active:self._mutate('CLOSE_REVOKE',self._recover_rows)
  finally:self._unlock()
 def __enter__(self):return self
 def __exit__(self,*_):self.close()

def bind_anchored_gateway(gateway,ledger,run,*,synthetic=False):
 """One authoritative historical admission, using the existing gateway wrapper.
 No supervisor-side charge/reset/import logic; test domains never bind live URLs.
 """
 from budget import guard_gateway
 from contract import Contract
 from urllib.parse import urlsplit
 if not isinstance(ledger,HistoryBudget):raise ValueError('live_gateway_requires_history_adapter')
 p=gateway.policy;u=urlsplit(p.upstream_url)
 if u.scheme!='https' or u.path!='/v1/chat/completions' or u.username or u.password or u.query or u.fragment:raise ValueError('unapproved_endpoint')
 if ledger.identity['domain']=='TEST':
  if not synthetic or u.hostname not in ('offline.invalid','localhost','127.0.0.1'):raise ValueError('test_domain_unavailable_live')
 elif synthetic or p.upstream_url!='https://api.openai.com/v1/chat/completions':raise ValueError('live_endpoint_required')
 if p.ceiling_micro_usd!=120000 or p.input_price_micro_per_million!=400000 or p.output_price_micro_per_million!=1600000 or p.approved_hosts!=(u.hostname,):raise ValueError('gateway_budget_or_host_mismatch')
 if p.model!=ledger.contract['model'] or p.max_model_calls!=4 or p.input_token_bound!=32000 or p.output_token_bound!=4096 or p.output_ceiling!=4096:raise ValueError('gateway_model_or_limits_mismatch')
 return guard_gateway(gateway,ledger,'coding',run,cost_bound=lambda _:request_worst_case(ledger.contract),estimator=Contract().estimate,token_bound=lambda _:(32000,4096))
