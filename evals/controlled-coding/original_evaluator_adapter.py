"""Narrow trusted adapter for byte-exact original acceptance assertions.
Assertions execute in current filtered namespace. Fixed lifecycle/test operations
use anonymous parent pipes; no generic command API, new server or provider access.
The app executes in a separate current filtered namespace and never sees /checks.
"""
import hashlib,importlib.util,json,os,select,signal,subprocess,sys,tempfile,time,types
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ORIGINAL=Path('/workspace/Fusion-phase2a/evals/implementation-evaluation')
HASHES={'acceptance.py':'9bafe8c124fe97dfe6280220228d27a21366ef379673d9dfdab30d7d061bb753','acceptance.mjs':'708c0230d42fb518a5f3442992241bdd9e5023b1c7f41505d4f0a5795a44d88a','service_bridge.py':'ddb46129202d7d097ab6495f5f7002975edc142c18865e34f56f6977b796ae95','ACCEPTANCE_TEST_SPEC.md':'b7fb86dcc97b32b1696e7c5660d9239b45a6edd1e1add5da7ac5528d8ee4033d'}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_original():
 for name,h in HASHES.items():
  if digest(ORIGINAL/name)!=h:raise ValueError('original_evaluator_changed:'+name)
 return HASHES

def inside():
 # This process is already in current user/net/PID/mount namespace + seccomp;
 # original hidden assertions are the only files under /checks.
 def rpc(action):
  print(json.dumps({'rpc':action}),flush=True);line=sys.stdin.readline()
  if not line:raise RuntimeError('trusted_supervisor_lost')
  response=json.loads(line)
  if not response.get('ok'):raise RuntimeError(response.get('error','supervisor_error'))
  return response
 class Service:
  def __init__(self,arm):self.arm=Path(arm)
  @property
  def socket(self):return self.arm/'runtime/app.sock'
  def start(self):rpc('start')
  def stop(self):rpc('stop')
 def command(arm,argv,**kwargs):
  if argv!=['/app/run-tests'] or kwargs!={'writable':False}:raise ValueError('unexpected_original_command')
  return ['TRUSTED_TESTS']
 def browser_command(*args,**kwargs):return ['BLOCKED_BROWSER']
 module=types.ModuleType('isolation');module.Service=Service;module.command=command;module.browser_command=browser_command;module.HERE=Path('/checks');sys.modules['isolation']=module
 spec=importlib.util.spec_from_file_location('original_assertions','/checks/acceptance.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
 def remote_run(argv,**kwargs):
  if argv==['BLOCKED_BROWSER']:
   r=rpc('browser');return subprocess.CompletedProcess(argv,r['returncode'],r['stdout'],r['stderr'])
  if argv!=['TRUSTED_TESTS']:raise ValueError('arbitrary_evaluator_command_denied')
  r=rpc('tests');return subprocess.CompletedProcess(argv,r['returncode'],r['stdout'],r['stderr'])
 original.subprocess=types.SimpleNamespace(run=remote_run)
 # Structural boundary evidence without exposing any credential contents.
 boundary={'provider_variables_absent':all(k not in os.environ for k in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GH_TOKEN','GITHUB_TOKEN')),'unrelated_workspace_absent':not Path('/workspace').exists(),'namespace_uid':os.getuid()}
 status=Path('/proc/self/status').read_text()
 boundary['no_new_privs']=next(x.split(':')[1].strip() for x in status.splitlines() if x.startswith('NoNewPrivs:'))=='1'
 boundary['zero_effective_capabilities']=next(x.split(':')[1].strip() for x in status.splitlines() if x.startswith('CapEff:'))=='0000000000000000'
 if not all(v for k,v in boundary.items() if k!='namespace_uid') or boundary['namespace_uid']!=65534:raise RuntimeError('assertion_boundary_failed')
 result=original.run(Path('/work'),Path('/checks/acceptance.mjs'),Path('/unused/browser-unavailable'))
 print(json.dumps({'result':result,'boundary':boundary}),flush=True)


def secure_argv(arm,argv,policy,*,bridge=False):
 from isolation import namespace_command
 # Existing namespace/filter construction, no alternative boundary or privileged
 # browser path. Exact additional mounts are product source/data and HTTP relay.
 mounts=[(arm/'app','/app')]
 if bridge:mounts.append((ORIGINAL/'service_bridge.py','/runtime/service_bridge.py'))
 cmd=namespace_command(None,arm/'tmp',[],seccomp_fd=policy.fileno(),command_override=argv,readonly_mounts=mounts)
 i=cmd.index('--remount-ro')
 extra=['--remount-ro','/work','--bind',str(arm/'data'),'/data','--dir','/runtime','--tmpfs','/home/agent','--setenv','HOME','/home/agent','--setenv','DATA_DIR','/data','--setenv','PORT','8080','--chdir','/app']
 if bridge:extra+=['--bind',str(arm/'runtime'),'/bridge']
 return cmd[:i]+extra+cmd[i:]

def evaluate(native_root,out,*,browser_dependency=None):
 from security_filter import export_filter
 from isolation import namespace_command
 verify_original();native_root=Path(native_root);out=Path(out);out.mkdir(mode=0o700,parents=True,exist_ok=False)
 for name in ('app','data','home','tmp','runtime','logs'):(out/name).mkdir(mode=0o700)
 env={'PATH':os.environ['PATH'],'HOME':str(out/'home'),'PYTHONDONTWRITEBYTECODE':'1','GIT_CONFIG_NOSYSTEM':'1'}
 for args in (['init','-q'],['apply','--check',str(native_root/'candidate.patch')],['apply',str(native_root/'candidate.patch')]):subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=out/'app',env=env,check=True,capture_output=True)
 captured=json.loads((native_root/'full-native-result.json').read_text());expected=captured['candidate_files']
 for name,h in expected.items():
  if digest(out/'app'/name)!=h:raise ValueError('independent_patch_hash')
  if bool((out/'app'/name).stat().st_mode&0o111)!=(captured['candidate_modes'][name]=='100755'):raise ValueError('independent_patch_mode')
 # Anonymous pipes connect only this trusted host lifecycle supervisor and the
 # isolated original assertions. No caller-supplied paths, argv or model content.
 service=None;service_log=None;child=None
 def stop():
  nonlocal service,service_log
  if service:
   if service.poll() is None:os.killpg(service.pid,signal.SIGTERM)
   try:service.wait(timeout=4)
   except subprocess.TimeoutExpired:os.killpg(service.pid,signal.SIGKILL);service.wait()
   service=None;service_log.close();service_log=None
  (out/'runtime/app.sock').unlink(missing_ok=True)
 def start():
  nonlocal service,service_log
  if service:raise ValueError('service_already_active')
  with tempfile.TemporaryFile() as policy:
   export_filter(policy);cmd=secure_argv(out,['/usr/bin/python3','/runtime/service_bridge.py'],policy,bridge=True)
   service_log=(out/'logs/evaluator-service.log').open('ab');service=subprocess.Popen(cmd,env=env,pass_fds=(policy.fileno(),),stdout=service_log,stderr=service_log,start_new_session=True)
  end=time.monotonic()+12
  while time.monotonic()<end:
   if service.poll() is not None:stop();raise RuntimeError('application_start_failed')
   if (out/'runtime/app.sock').exists():return
   time.sleep(.03)
  stop();raise RuntimeError('application_start_deadline')
 try:
  mounts=[(ROOT/'original_evaluator_adapter.py','/eval/adapter.py'),*( (ORIGINAL/n,'/checks/'+n) for n in HASHES)]
  with tempfile.TemporaryFile() as policy:
   export_filter(policy);cmd=namespace_command(None,out,[],seccomp_fd=policy.fileno(),command_override=[sys.executable,'-B','/eval/adapter.py','--inside'],readonly_mounts=mounts)
   child=subprocess.Popen(cmd,env=env,pass_fds=(policy.fileno(),),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  result=None;deadline=time.monotonic()+240
  while time.monotonic()<deadline:
   ready,_,_=select.select([child.stdout],[],[],.2)
   if not ready:
    if child.poll() is not None:break
    continue
   line=child.stdout.readline(2_000_000)
   if not line:break
   message=json.loads(line)
   if 'rpc' not in message:result=message;break
   action=message['rpc'];response={'ok':True}
   try:
    if action=='start':start()
    elif action=='stop':stop()
    elif action=='browser':
     if browser_dependency is None:response.update(returncode=125,stdout='',stderr='BLOCKED: no verified browser dependency selected')
     else:
      from verified_browser_runtime import mounts
      browser_mounts,provenance=mounts(browser_dependency)
      playwright=Path('/workspace/Fusion/node_modules/.pnpm/playwright-core@1.60.0/node_modules/playwright-core')
      work=out/'browser-work';work.mkdir(exist_ok=True)
      entries=[*browser_mounts,(ROOT/'original_browser_runtime.mjs','/eval/browser.mjs'),(playwright,'/opt/playwright'),(out/'runtime','/bridge'),(Path('/etc/fonts'),'/etc/fonts')]
      with tempfile.TemporaryFile() as policy:
       export_filter(policy);argv=namespace_command(None,work,[],seccomp_fd=policy.fileno(),command_override=[__import__('shutil').which('node'),'/eval/browser.mjs'],readonly_mounts=entries)
       browser=subprocess.run(argv,env=env,pass_fds=(policy.fileno(),),input=(ORIGINAL/'acceptance.mjs').read_bytes(),capture_output=True,timeout=35)
      response.update(returncode=browser.returncode,stdout=browser.stdout.decode(),stderr=browser.stderr.decode())
      (out/'logs/browser-provenance.json').write_text(json.dumps({k:v for k,v in provenance.items() if k!='files'},indent=2)+'\n')
    elif action=='tests':
     with tempfile.TemporaryFile() as policy:
      export_filter(policy);test=subprocess.run(secure_argv(out,['/app/run-tests'],policy),env=env,pass_fds=(policy.fileno(),),capture_output=True,text=True,timeout=45)
     response.update(returncode=test.returncode,stdout=test.stdout,stderr=test.stderr)
    else:raise ValueError('unknown_fixed_operation')
   except Exception as e:response={'ok':False,'error':type(e).__name__+': '+str(e)}
   child.stdin.write(json.dumps(response)+'\n');child.stdin.flush()
  if result is None:raise RuntimeError('isolated_original_evaluator_failed_or_timed_out')
  child.stdin.close();child.wait(timeout=10);stderr=child.stderr.read();(out/'logs/assertions-stderr.log').write_text(stderr)
  if child.returncode:raise RuntimeError('assertions_process_failed')
  for name,h in expected.items():
   if digest(out/'app'/name)!=h:raise ValueError('graded_source_changed')
   if bool((out/'app'/name).stat().st_mode&0o111)!=(captured['candidate_modes'][name]=='100755'):raise ValueError('graded_mode_changed')
  result.update(classification='BYTE-EXACT ORIGINAL ASSERTIONS under current isolated adapter',original_hashes=HASHES,source_patch_sha256=digest(native_root/'candidate.patch'))
  categories=result['result']['categories'];result['non_browser_passed']=all(c['passed'] for c in categories if c['category']!='browser_functionality')
  result['browser_status']='VERIFIED' if next(c for c in categories if c['category']=='browser_functionality')['passed'] else ('BLOCKED: no browser dependency' if browser_dependency is None else 'FAILED: real browser assertion/runtime; see private logs');result['complete_acceptance']=result['result']['completion']
  (out/'original-acceptance-result.json').write_text(json.dumps(result,indent=2)+'\n');return result
 finally:
  stop()
  if child and child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait()

if __name__=='__main__':
 if sys.argv[1:]==['--inside']:inside()
 else:
  import argparse
  p=argparse.ArgumentParser();p.add_argument('--browser-dependency',type=Path);p.add_argument('--native-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=evaluate(a.native_root,a.out,browser_dependency=a.browser_dependency);print(json.dumps(r,indent=2))
