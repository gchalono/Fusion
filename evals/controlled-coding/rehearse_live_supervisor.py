"""FNXC:LiveCoding 2026-11-10-06:16: Actual-supervisor CLI acceptance driver.
All approvals, keys, ledgers and responses here are explicitly TEST-domain. Real
historical anchor is replayed read-only; authoritative continuation is never changed.
"""
import argparse,copy,json,os,signal,subprocess,sys,time
from pathlib import Path
from contract import canonical
from history_budget import HistoryBudget
from live_supervisor import ROOT,REPO,TEST_SELECTOR,prepare_spec,open_ledger
from operator_auth import make_test_trust,sign_payload,clean_env
from task_manager_full_native import plan
from offline_eval import start_stub

def setup(root,case):
 root.mkdir(mode=0o700,parents=True);state=root/'state';state.mkdir(mode=0o700);(state/'.synthetic-rehearsal').touch()
 HistoryBudget.initialize(state/'continuation.sqlite3',state/'witness.json',test_key=TEST_SELECTOR)
 trust=make_test_trust(root/'TEST-signing');spec=prepare_spec(test_state=state)
 payload={'spec':spec,'transport':{'metadata_sha256':'0'*64,'provider_side_cap_confirmed':False}}
 if case=='expired':spec['expires_at']=time.time()-1
 if case=='wrong-source':spec['source_commit']='f'*40
 if case=='wrong-config':spec['config_sha256']='f'*64
 if case=='wrong-ledger':spec['ledger_id']='f'*64
 if case=='wrong-model':spec['model']='unapproved-model'
 if case=='over-budget':spec['limits']['run_micro_usd']=120001
 envelope=sign_payload(payload,trust.parent/'TEST-operator.key',trust.parent/'operator.pub')
 if case=='invalid-approval':envelope['payload']['spec']['nonce']='ALTERED_WITHOUT_SIGNATURE'
 approval=root/'TEST-approval.json';approval.write_bytes(canonical(envelope))
 tls=root/'transport';tls.mkdir(mode=0o700);(tls/'.offline-test').touch()
 return state,trust,approval,tls

def cli_args(root,state,trust,approval,tr,out='job'):
 return [sys.executable,'-B',str(ROOT/'live_supervisor.py'),'run','--approval',str(approval),'--out',str(root/out),'--test-state',str(state),'--trust',str(trust),'--synthetic-transport',str(tr)]

def process_tree(parent):
 rows={}
 for line in subprocess.check_output(['ps','-eo','pid=,ppid=,stat=,comm='],env=clean_env(),text=True).splitlines():
  v=line.split()
  if len(v)>=4:rows[int(v[0])]={'parent':int(v[1]),'state':v[2],'command':v[3]}
 selected={parent}
 while True:
  more=selected|{p for p,d in rows.items() if d['parent'] in selected}
  if more==selected:return {p:rows[p] for p in selected if p in rows}
  selected=more

PROBE="""python3 - <<'LOCAL_PROBE'
import os,pathlib,socket,json
P=pathlib.Path
c={'no_provider_env':all(k not in os.environ for k in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GH_TOKEN','GITHUB_TOKEN')),'no_host_files':not P('/workspace').exists(),'no_hidden_evaluator':not P('/checks').exists(),'no_provider_proc':True,'no_provider_descriptor':True}
for f in P('/proc').glob('[0-9]*/environ'):
 try:
  if b'OPENAI_API_KEY=' in f.read_bytes():c['no_provider_proc']=False
 except OSError:pass
for f in P('/proc/self/fd').iterdir():
 try:
  if 'fusion-gateway-credential' in os.readlink(f):c['no_provider_descriptor']=False
 except OSError:pass
s=socket.socket();s.settimeout(.1)
try:s.connect(('192.0.2.1',443));c['no_direct_provider_network']=False
except OSError:c['no_direct_provider_network']=True
finally:s.close()
print(json.dumps(c));assert all(c.values())
LOCAL_PROBE"""

def execute(root,case,tokenizer):
 state,trust,approval,tls=setup(root,case);_,p=plan(tokenizer);contacted=__import__('threading').Event();release=__import__('threading').Event()
 def reply(body):
  i=sum(bool(m.get('tool_calls')) for m in body['messages'] if m['role']=='assistant')
  if case=='crash':contacted.set();release.wait(30)
  if case=='security' and i==0:
   return {'role':'assistant','tool_calls':[{'index':0,'id':'TEST_SECURITY','type':'function','function':{'name':'bash','arguments':json.dumps({'command':PROBE})}}]},'tool_calls'
  if case=='security':return {'role':'assistant','content':'SYNTHETIC security probe finished'},'stop'
  if i<3:return p['deltas'][i],'tool_calls'
  if case=='budget':return {'role':'assistant','tool_calls':[{'index':0,'id':'TEST_CAP','type':'function','function':{'name':'read','arguments':'{"path":"README.md"}'}}]},'tool_calls'
  return {'role':'assistant','content':'SYNTHETIC completion; not real-model ability'},'stop'
 def interrupted(body,n):return 200,'text/event-stream',('data: '+json.dumps({'model':body['model'],'choices':[{'index':0,'delta':{'content':'SYNTHETIC partial'},'finish_reason':None}]})+'\n\n').encode()
 server,contacts=start_stub(tls,script=reply,response=interrupted if case=='interrupted' else None)
 transport={'root':str(tls),'url':f'https://localhost:{server.server_port}/v1/chat/completions','ca':str(tls/'tls.crt'),'key':str(tls/'upstream-key')}
 if case=='wrong-endpoint':transport['url']='https://api.openai.com/v1/chat/completions'
 if case=='missing-credential':(tls/'upstream-key').unlink()
 tr=root/'transport.json';tr.write_bytes(canonical(transport));args=cli_args(root,state,trust,approval,tr)
 try:
  if case=='crash':
   process=subprocess.Popen(args,cwd=REPO,env=clean_env(),stdout=(root/'cli.stdout').open('w'),stderr=(root/'cli.stderr').open('w'),start_new_session=True)
   if not contacted.wait(30):process.kill();process.wait();raise AssertionError('native dispatch not reached')
   owned=process_tree(process.pid)
   other=subprocess.run(cli_args(root,state,trust,approval,tr,'concurrent'),cwd=REPO,env=clean_env(),capture_output=True,text=True,timeout=10);assert other.returncode!=0
   process.kill();process.wait(timeout=10);release.set()
   recovery=subprocess.run([sys.executable,'-B',str(ROOT/'live_supervisor.py'),'recover','--test-state',str(state)],cwd=REPO,env=clean_env(),capture_output=True,text=True,timeout=15);assert recovery.returncode==0,recovery.stdout
   again=subprocess.run(cli_args(root,state,trust,approval,tr,'replay'),cwd=REPO,env=clean_env(),capture_output=True,text=True,timeout=10);assert again.returncode!=0
   deadline=time.monotonic()+5
   while time.monotonic()<deadline:
    live={pid:v for pid,v in process_tree(os.getpid()).items() if pid in owned and not v['state'].startswith('Z')}
    if not live:break
    time.sleep(.05)
   # Namespace children die with their gateway parent, including transport worker.
   running=[]
   for pid in owned:
    status=Path(f'/proc/{pid}/stat')
    if status.exists() and status.read_text().split(') ',1)[1].split()[0]!='Z':running.append(pid)
   assert not running,running
   with open_ledger(state) as b:snapshot=b.snapshot()
   assert len(contacts)==1 and snapshot['requests']==1 and snapshot['exposure_micro_usd']==30876
   receipt={'case':case,'exclusive_admission':True,'crash_returncode':process.returncode,'restart_terminal_no_replay':True,'request_count':1,'owned_processes_running':running,'provider_inference_requests':0}
  else:
   c=subprocess.run(args,cwd=REPO,env=clean_env(),capture_output=True,text=True,timeout=180);(root/'cli.stdout').write_text(c.stdout);(root/'cli.stderr').write_text(c.stderr)
   negative=case in ('invalid-approval','expired','wrong-source','wrong-config','wrong-ledger','wrong-model','wrong-endpoint','missing-credential','over-budget')
   if negative:
    assert c.returncode!=0 and not contacts,(case,c.stdout,len(contacts));receipt={'case':case,'refused_before_dispatch':True,'provider_inference_requests':0}
   else:
    assert c.returncode==0,(c.stdout,c.stderr);r=json.loads((root/'job/result.json').read_text());assert r['request_count']==len(contacts)<=4;assert r['cleanup']['approval_run_terminal'] and r['cleanup']['gateway_revoked']
    if case=='full':
     assert r['native_loop_completed'] and r['non_browser_passed'] and r['patch_sha256']=='df383ba28a82be9f2a07b36d188a4f4bec11f551f1013634186c3752c2b0ba6c',r
     audit=(root/'job/agent-stdout.txt').read_text();assert all('"tool":"'+name+'"' in audit for name in ('read','write','bash'))
     replay=subprocess.run(cli_args(root,state,trust,approval,tr,'replay'),cwd=REPO,env=clean_env(),capture_output=True,text=True,timeout=10);assert replay.returncode!=0 and len(contacts)==4
    if case=='budget':assert not r['native_loop_completed'] and r['request_count']==4 and r['evaluator_invoked'] and r['non_browser_passed'] and r['termination']=='inconclusive: cap-limited',r
    if case=='interrupted':assert not r['native_loop_completed'] and r['evaluator_invoked'];assert all(s[2]=='UNCERTAIN' for s in r['ledger']['settlements'])
    if case=='security':
     audit=(root/'job/agent-stdout.txt').read_text();assert 'no_provider_descriptor' in audit and 'false' not in audit.split('no_provider_descriptor',1)[1].split('LOCAL_PROBE',1)[0][:80],audit[-1000:]
    receipt={k:r[k] for k in ('request_count','native_loop_completed','termination','evaluator_invoked','non_browser_passed','provider_inference_requests')};receipt['case']=case
    secret=(tls/'upstream-key').read_bytes().strip()
    for f in (root/'job').rglob('*'):
     if f.is_file():assert secret not in f.read_bytes(),'synthetic provider credential reflected:'+str(f)
  (root/'receipt.json').write_bytes(canonical(receipt));return receipt
 finally:release.set();server.shutdown();server.server_close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--tokenizer',type=Path,default=Path('/workspace/fusion-offline-tokenizer/node_modules/js-tiktoken/dist/index.js'));p.add_argument('--cases',default='full,budget,interrupted,security,crash,invalid-approval,expired,wrong-source,wrong-config,wrong-ledger,wrong-model,wrong-endpoint,missing-credential,over-budget');a=p.parse_args();a.out.mkdir(mode=0o700,parents=True,exist_ok=False);receipts=[]
 for case in a.cases.split(','):
  r=execute(a.out/case,case,a.tokenizer);receipts.append(r);print(json.dumps(r),flush=True)
 (a.out/'rehearsal-receipts.json').write_bytes(canonical(receipts))
