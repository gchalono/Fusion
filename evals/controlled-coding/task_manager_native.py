"""FNXC:TaskManagerOfflineValidation 2026-11-09-20:38:
TEST DOUBLE native wire/coding validation; no live transport entry point.
Default remains Arm A / 16000. Explicit expanded_offline opts into the verified
operator-directed Experiment 2 revision and permits frozen A/B/C inputs.
A small bounded tool payload is a deliberately incomplete implementation control,
not a claimed correct task manager or model capability result.
"""
import difflib,json,os,secrets,subprocess,sys,threading
from pathlib import Path
from task_manager_adapter import load_arm,experiment_contract,TASK,sha
from contract import canonical
from budget import AggregateBudget
from execution import run_command,runtime_mounts,coding_command
from pilot import spawn_broker,request_admin
from offline_eval import start_stub

ROOT=Path(__file__).resolve().parent
CONTENT='import sqlite3\nfrom http.server import HTTPServer,SimpleHTTPRequestHandler\ndb=sqlite3.connect("tasks.sqlite3")\ndb.execute("CREATE TABLE IF NOT EXISTS tasks(title TEXT)")\nHTTPServer(("127.0.0.1",8080),SimpleHTTPRequestHandler).serve_forever()\n'


def script(body,variant="coding"):
 if any(m['role']=='tool' for m in body['messages']):
  delta={'role':'assistant','content':'TEST DOUBLE: native coding tool completed. This is an incomplete control, not a finished task manager.'};finish='stop'
 elif variant=='security':
  command='test ! -e /checks && test ! -e /workspace/phase2n-evaluation && test ! -e /workspace/tm-resume-evidence/host-canary && test -z "${OPENAI_API_KEY+x}" && ! timeout 1 bash -c "echo >/dev/tcp/192.0.2.1/443" && echo TEST_DOUBLE_SECURITY_PASS'
  delta={'role':'assistant','tool_calls':[{'index':0,'id':'TEST_DOUBLE_SECURITY','type':'function','function':{'name':'bash','arguments':json.dumps({'command':command},separators=(',',':'))}}]};finish='tool_calls'
 elif variant=='unauthorized':
  delta={'role':'assistant','tool_calls':[{'index':0,'id':'TEST_DOUBLE_DENY','type':'function','function':{'name':'unauthorized_test_tool','arguments':'{}'}}]};finish='tool_calls'
 else:
  delta={'role':'assistant','tool_calls':[{'index':0,'id':'TEST_DOUBLE_WRITE','type':'function','function':{'name':'write','arguments':json.dumps({'path':'application.py','content':CONTENT},separators=(',',':'))}}]};finish='tool_calls'
 # Conservative bytes bound, not a fabricated provider token count.
 if len(canonical(delta))>512:raise ValueError('TEST_DOUBLE_output_may_exceed_active_512_bound')
 return delta,finish


def reject_output_secrets(root,*values):
 # Generated local TEST DOUBLE keys only; never provider credentials.
 for name in ('local-token','upstream-key'):
  secret=(Path(root)/name).read_bytes().strip()
  if secret and any(secret in value for value in values):raise ValueError('TEST_DOUBLE_token_in_collected_output')

def persist_checked_outputs(root, report, raw):
 root=Path(root);reject_output_secrets(root,raw,report['stdout'],report['stderr'])
 for name in ('stdout','stderr'):(root/('agent-'+name+'.txt')).write_bytes(report[name])


def run(root,runtime,*,timeout=90,variant="coding",pause=None,broker_hook=None,arm="A",expanded_offline=False,script_override=None,expected_requests=2,capture_all=False,offline_768=False,readiness=False,response_override=None):
 if arm not in "ABC" or len(arm)!=1 or (arm!="A" and not expanded_offline):raise ValueError("arm_requires_scoped_offline_revision")
 if readiness and (arm!='A' or offline_768 or not expanded_offline):raise ValueError('readiness_requires_expanded_A_without_768')
 if offline_768 and not expanded_offline:raise ValueError('profile_requires_expanded_experiment2')
 root=Path(root);root.mkdir(parents=True,exist_ok=False);root.chmod(0o700);(root/'.offline-test').touch()
 prompt=load_arm('/workspace/phase2m-genuine-success','/workspace/phase2n-evaluation/frozen',arm)
 (root/'objective.txt').write_bytes(prompt)
 from task_manager_token_revision import offline_contract
 d=offline_contract() if expanded_offline else experiment_contract()
 from offline_output_profile import NAME
 from readiness_profile import ceiling,NAME as READINESS_NAME
 if offline_768:d['offline_output_profile']=NAME
 if readiness:d['readiness_profile']=READINESS_NAME
 output_limit=ceiling(d,offline=True)
 (root/'experiment.json').write_bytes(canonical(d));AggregateBudget(root/'experiment.db',experiment_contract=d)
 wires=[]
 def observe(body):
  wires.append(body);(root/f'native-wire-{len(wires):02}.json').write_bytes(canonical(body))
 workspace=root/'workspace'
 subprocess.run(['git','-c','core.hooksPath=/dev/null','clone','--quiet','--no-local','/workspace/phase2n-evaluation/frozen/empty-seed',str(workspace)],check=True,capture_output=True,env={'PATH':os.environ['PATH'],'HOME':str(root)})
 # Validate the trusted seed BEFORE untrusted tools can alter Git configuration.
 # Never invoke host Git on the candidate's potentially modified .git afterward.
 if capture_all and subprocess.check_output(['git','ls-tree','--name-only','HEAD'],cwd=workspace).strip():raise ValueError('capture_requires_frozen_empty_seed')
 server,contacts=start_stub(root,script=script_override or (lambda body:script(body,variant)),observe=observe,pause=pause,response=response_override)
 process=None;log=None;watch_stop=threading.Event();abort=threading.Event();report=None
 try:
  process,log=spawn_broker(root,TASK+':'+arm)
  if broker_hook is not None:broker_hook(process)
  def watch():
   while not watch_stop.wait(.05):
    if process.poll() is not None:abort.set();return
  thread=threading.Thread(target=watch,daemon=True);thread.start()
  mounts=[(ROOT/'coding-agent.mts','/eval/coding-agent.mts'),(root/'local-token','/run/local-token'),(root/'objective.txt','/run/objective.txt'),*runtime_mounts(runtime)]
  if offline_768:mounts.append((root/'experiment.json','/run/offline-profile.json'))
  if readiness:mounts.append((root/'experiment.json','/run/readiness-profile.json'))
  report=run_command(root/'gateway.sock',workspace,coding_command(runtime,d['model']),mounts=mounts,timeout=min(timeout,300),abort_event=abort,app_alias=offline_768 or readiness)
  candidate=workspace/'application.py';raw=candidate.read_bytes() if candidate.is_file() and not candidate.is_symlink() else b''
  persist_checked_outputs(root,report,raw)
  patch=''.join(difflib.unified_diff([],raw.decode().splitlines(True),fromfile='/dev/null',tofile='b/application.py'))
  candidate_files={};candidate_modes={}
  if capture_all:
   patch=''
   for file in sorted(workspace.rglob('*')):
    relative=file.relative_to(workspace)
    if '.git' in relative.parts:continue
    if file.is_symlink():raise ValueError('candidate_symlink')
    if not file.is_file():continue
    if file.suffix not in ('.py','.md','.html','.js','.css','.sh') and str(relative) not in ('run-app','run-tests'):raise ValueError('unexpected_candidate_artifact:'+str(relative))
    content=file.read_bytes();reject_output_secrets(root,content);candidate_files[str(relative)]=sha(content)
    mode='100755' if file.stat().st_mode&0o111 else '100644';candidate_modes[str(relative)]=mode
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./-' for c in str(relative)):raise ValueError('unsafe_patch_path')
    patch+='diff --git a/'+str(relative)+' b/'+str(relative)+'\nnew file mode '+mode+'\n'
    patch+=''.join(difflib.unified_diff([],content.decode().splitlines(True),fromfile='/dev/null',tofile='b/'+str(relative)))
  (root/'candidate.patch').write_text(patch)
  if process.poll() is None:request_admin(root,'finish' if report['exit_code']==0 and len(contacts)==expected_requests else 'abort')
  else:
   recovered=AggregateBudget(root/'experiment.db');recovered.recover_uncertain();recovered.control_run('coding',TASK+':'+arm,'INCOMPLETE')
  result={'classification':'TEST DOUBLE native Pi run; incomplete implementation control; NOT model performance',
    'arm':arm,'variant':variant,'candidate_files':candidate_files,'candidate_modes':candidate_modes,'input_sha256':sha(prompt),'exit_code':report['exit_code'],'timed_out':report['timed_out'],'aborted':report['aborted'],'elapsed_seconds':report['elapsed_seconds'],
    'local_model_wire_requests':len(contacts),'real_provider_requests':0,'provider_usage':None,'actual_provider_cost_usd':'0.00',
    'coding_tool_modified_files':bool(raw),'candidate_sha256':sha(raw),'patch_sha256':sha(patch.encode()),
    'tool_audit_present':b'OFFLINE_AUDIT_ONLY' in report['stdout'],'native_loop_completed':len(contacts)==expected_requests and any(m['role']=='tool' for m in wires[-1]['messages']) and report['exit_code']==0,
    'ledger':AggregateBudget(root/'experiment.db').snapshot(),'active_cumulative_bound':d['frozen_coding_token_limit'],'active_offline_output_bound':output_limit,
    'full_task_completion':False,'browser_grading':'UNVERIFIED / independent gate',
    'wire_files':[str(root/f'native-wire-{i:02}.json') for i in range(1,len(wires)+1)]}
  (root/'result.json').write_bytes(canonical(result));return result
 finally:
  watch_stop.set()
  if process is not None:
   if process.poll() is None:
    try:request_admin(root,'abort')
    except Exception:process.terminate()
   process.wait(timeout=10)
  if log:log.close()
  server.shutdown();server.server_close()

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--arm',choices=list('ABC'),default='A');p.add_argument('--expanded-offline',action='store_true');p.add_argument('--variant',choices=['coding','security','unauthorized'],default='coding');a=p.parse_args();r=run(a.root,a.runtime,variant=a.variant,arm=a.arm,expanded_offline=a.expanded_offline);print(json.dumps({k:r[k] for k in ('native_loop_completed','exit_code','local_model_wire_requests','coding_tool_modified_files','actual_provider_cost_usd')}))
