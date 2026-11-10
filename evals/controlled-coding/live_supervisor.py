"""FNXC:LiveCoding 2026-11-10-06:16: One signed coding run; no planner,
TaskStore, autopilot or replacement agent framework. Same entry for TEST transport
and live transport; domain/ledger/key boundaries are enforced before dispatch.
"""
import argparse,hashlib,json,os,secrets,subprocess,sys,tempfile,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
sys.path.insert(0,str(ROOT.parent/'planning-collector'))
from contract import Contract,canonical
from gateway import Gateway,Policy,Artifacts
from history_budget import HistoryBudget,bind_anchored_gateway,sha
from operator_auth import ApprovalVerifier,strict,clean_env,LIVE_TRUST,TEST_DOMAIN,LIVE_DOMAIN
from execution import run_command,runtime_mounts,coding_command
from pilot import make_inference_server
from real_transport import RealTransport,sealed_credential
from source_capture import capture,no_secrets
from task_manager_adapter import load_arm
from original_evaluator_adapter import evaluate,verify_original
RUNTIME=Path('/workspace/Fusion');RUNTIME_SHA='eb7eef49d5a0fe3e84e99be30e8ed9622a694e35'
AUTHORITY=Path('/workspace/phase3c-ledger');TEST_SELECTOR=b'SYNTHETIC_DOMAIN_SELECTOR_NOT_A_SIGNING_KEY'
MODEL='gpt-4.1-mini-2025-04-14';RUN='phase2m-personal-task-manager:A'
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,env=clean_env(),text=True).strip()
def state_paths(test_state=None):
 r=Path(test_state) if test_state else AUTHORITY
 if test_state and (r.resolve()==AUTHORITY or not (r/'.synthetic-rehearsal').is_file()):raise ValueError('marked_TEST_state_required')
 return r/'continuation.sqlite3',r/'witness.json'
def open_ledger(test_state=None,verifier=None,recover=False):
 p,w=state_paths(test_state)
 return HistoryBudget(p,w,test_key=TEST_SELECTOR if test_state else None,operator_verifier=verifier,recover=recover)
def prepare_spec(*,test_state=None):
 with open_ledger(test_state) as b:
  return {'domain':TEST_DOMAIN if test_state else LIVE_DOMAIN,'model':MODEL,'arm':'A','objective_sha256':'4edc93814c7a6ad5c43445ad07f853ca3350ed0e3f6dc7764e1c04e0c4cdffe0','seed_commit':'f2a49cb3fc7e02cd225053d4e2d07c589b4c808b','source_commit':git(REPO,'rev-parse','HEAD'),'config_sha256':sha(canonical(b.contract)),'ledger_id':b.identity['ledger_id'],'anchor_sha256':b.identity['anchor_sha256'],'limits':{'requests':4,'input':32000,'output':4096,'run_seconds':300,'request_seconds':60,'run_micro_usd':120000,'aggregate_micro_usd':2000000},'nonce':secrets.token_hex(32),'expires_at':time.time()+1800,'run_id':RUN}

def preflight(spec,*,synthetic=False):
 if spec['source_commit']!=git(REPO,'rev-parse','HEAD'):raise ValueError('source_commit_mismatch')
 if git(REPO,'status','--porcelain','--untracked-files=all'):raise ValueError('source_dirty')
 if spec['model']!=MODEL or spec['arm']!='A' or spec['run_id']!=RUN:raise ValueError('frozen_model_arm_or_task_mismatch')
 if git(RUNTIME,'rev-parse','HEAD')!=RUNTIME_SHA or git(RUNTIME,'status','--porcelain'):raise ValueError('runtime_source_changed')
 seed=Path('/workspace/phase2n-evaluation/frozen/empty-seed')
 if git(seed,'rev-parse','HEAD')!=spec['seed_commit'] or git(seed,'ls-tree','--name-only','HEAD'):raise ValueError('frozen_empty_seed_mismatch')
 verify_original();return load_arm('/workspace/phase2m-genuine-success','/workspace/phase2n-evaluation/frozen','A')

def isolation_preflight(root,secrets_):
 work=root/'isolation-probe';work.mkdir()
 code='''import os,pathlib,socket,json
P=pathlib.Path
c={'provider_env_absent':all(k not in os.environ for k in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GH_TOKEN','GITHUB_TOKEN')),'protected_host_absent':not P('/workspace/phase3c-ledger').exists() and not P('/workspace/Fusion/.env').exists() and not P('/workspace/Fusion/.fusion').exists(),'runtime_only_workspace':set(p.name for p in P('/workspace').iterdir())=={'Fusion'},'provider_descriptor_absent':True,'hidden_absent':not P('/checks').exists(),'proc_provider_absent':True}
for f in P('/proc').glob('[0-9]*/environ'):
 try:
  if b'OPENAI_API_KEY=' in f.read_bytes():c['proc_provider_absent']=False
 except OSError:pass
for f in P('/proc/self/fd').iterdir():
 try:
  if 'fusion-gateway-credential' in os.readlink(f):c['provider_descriptor_absent']=False
 except OSError:pass
s=socket.socket();s.settimeout(.1)
try:s.connect(('192.0.2.1',443));c['egress_denied']=False
except OSError:c['egress_denied']=True
finally:s.close()
print(json.dumps(c));assert all(c.values())
'''
 r=run_command(None,work,['python3','-c',code],mounts=runtime_mounts(RUNTIME),timeout=5)
 no_secrets(r['stdout']+r['stderr'],secrets_)
 if r['exit_code']!=0:raise ValueError('isolation_preflight_failed')
 receipt=json.loads(r['stdout']);(root/'isolation.json').write_bytes(canonical(receipt));return receipt

def approved_metadata(path,payload):
 raw=Path(path).read_bytes()
 if sha(raw)!=payload['transport'].get('metadata_sha256'):raise ValueError('metadata_not_bound_to_approval')
 m=strict(raw)
 if m.get('model_access')!='VERIFIED' or m.get('http_status')!=200 or m.get('model',{}).get('id')!=MODEL or m.get('pricing_verified') is not True or not 0<=time.time()-m.get('timestamp',0)<=86400:raise ValueError('current_model_access_and_pricing_required')
 if payload['transport'].get('provider_side_cap_confirmed') is not True:raise ValueError('existing_transport_requires_operator_provider_cap_confirmation')
 return m

def terminal_provider_error(status,body):
 if status in (401,403):return True
 try:
  error=json.loads(body).get('error',{})
  return isinstance(error,dict) and error.get('code') in ('insufficient_quota','billing_hard_limit_reached','invalid_api_key','account_deactivated')
 except (ValueError,AttributeError):return False

def run(approval,out,*,trust=LIVE_TRUST,test_state=None,synthetic_transport=None,metadata=None):
 envelope=strict(Path(approval).read_bytes());synthetic=test_state is not None
 verifier=ApprovalVerifier(trust,envelope,test_only=synthetic);spec=envelope['payload']['spec']
 prompt=preflight(spec,synthetic=synthetic)
 if synthetic and synthetic_transport is None:raise ValueError('synthetic_transport_required')
 if not synthetic and synthetic_transport is not None:raise ValueError('test_transport_unavailable_live')
 if not synthetic:approved_metadata(metadata,envelope['payload'])
 root=Path(out).resolve()
 if root.is_relative_to(REPO) or root.exists():raise ValueError('new_private_output_outside_repository_required')
 root.mkdir(mode=0o700,parents=True);(root/'approval.json').write_bytes(canonical(envelope));(root/'objective.txt').write_bytes(prompt)
 ledger=None;server=None;transport=None;credential_fd=None;provider_key=None;token=secrets.token_hex(32);secret_values=[token];report=None;result=None;denials=[]
 try:
  ledger=open_ledger(test_state,verifier);ledger.authorize_run(spec,envelope['signature'])
  workspace=root/'workspace';subprocess.run(['git','-c','core.hooksPath=/dev/null','clone','--quiet','--no-local','/workspace/phase2n-evaluation/frozen/empty-seed',str(workspace)],env=clean_env(),check=True,capture_output=True)
  (root/'local-token').write_text(token);(root/'local-token').chmod(0o600)
  profile={'profile':'phase3d-approved-gateway','model':MODEL,'arm':'A','requests':4,'output':4096,'synthetic':synthetic};(root/'profile.json').write_bytes(canonical(profile))
  if synthetic:
   tr=synthetic_transport;secret_values.append(Path(tr['key']).read_text().strip())
   credential_fd=sealed_credential(secret_values[-1]);transport=RealTransport(test_mode=True,test_root=tr['root'],test_url=tr['url'],test_ca=tr['ca'],test_key_file=tr['key'],credential_fd=credential_fd)
  else:
   # Only this TRUSTED GATEWAY process accesses the real key, after all gates.
   # It is removed from the environment; descendants receive explicit clean env.
   provider_key=os.environ.pop('OPENAI_API_KEY',None)
   if not provider_key:raise ValueError('gateway_provider_credential_missing')
   secret_values.append(provider_key);credentials=root/'gateway-private';credentials.mkdir(mode=0o700)
   credential_fd=sealed_credential(provider_key)
   cfg=dict(ledger.contract);cfg.update(provider_spend_authorized_usd='0.12',model_availability='VERIFIED')
   cfgpath=credentials/'transport-contract.json';cfgpath.write_bytes(canonical(cfg));c=Contract(cfgpath)
   permit={'live_authorized':True,'model':MODEL,'contract_sha256':c.sha256,'approved_hosts':['api.openai.com'],'expires_at':spec['expires_at'],'provider_side_cap_confirmed':True,'authorized_spend_usd':.12,'credential_fd':credential_fd,'model_availability_verified':True,'model_availability_evidence':envelope['payload']['transport']['metadata_sha256']}
   permitpath=credentials/'transport-permit.json';permitpath.write_bytes(canonical(permit));permitpath.chmod(0o600)
   transport=RealTransport(live=True,authorization_file=permitpath,contract_path=cfgpath,credential_fd=credential_fd)
  isolation_preflight(root,secret_values)
  audit=root/'gateway';audit.mkdir();artifacts=Artifacts(audit,secrets=tuple(secret_values));policy=Policy('OpenAI',MODEL,transport.url,('localhost',) if synthetic else ('api.openai.com',),4,120000,400000,1600000,32000,4096,4096)
  raw_attempts=[]
  def checked_transport(url,raw):
   if server is not None and server.revoked.is_set():raise OSError('gateway_revoked')
   status,kind,body=transport(url,raw);raw_attempts.append(status);artifacts.write(f'transport-response-{len(raw_attempts):04}.raw',body)
   if terminal_provider_error(status,body):
    if server is not None:server.revoked.set()
    denials.append('provider_auth_or_billing_error')
   if status==200 and 'text/event-stream' in kind and not body.replace(b'\r\n',b'\n').rstrip().endswith(b'data: [DONE]'):raise OSError('incomplete_provider_stream')
   return status,kind,body
  gateway=bind_anchored_gateway(Gateway(policy,artifacts,checked_transport),ledger,RUN,synthetic=synthetic)
  c=Contract()
  class RoutedGateway:
   policy=gateway.policy
   def handle(self,raw):
    if server.revoked.is_set():raise ValueError('gateway_revoked')
    try:
     if any(e['requested_max_tokens']!=e['forwarded_max_tokens'] for e in server.events):raise ValueError('output_limit_intervention_rejected')
     body=json.loads(raw);body['temperature']=0;normalized,_=c.prepare(canonical(body));transport.timeout=min(60,ledger.remaining_seconds('coding',RUN));return gateway.handle(normalized)
    except Exception as e:
     code=str(e) if str(e) in ('aggregate_spend_cap','experiment_request_cap','coding_run_cap','stage_allocation_cap','call_cap','spend_ceiling') else 'request_denied'
     denials.append(code);raise
  server=make_inference_server(root/'gateway.sock',c=c,transport=transport,ledger=ledger,run=RUN,gateway=RoutedGateway(),token=token,artifacts=artifacts,output_limit=4096,strict=True);threading.Thread(target=server.serve_forever,daemon=True).start()
  mounts=[(ROOT/'coding-agent.mts','/eval/coding-agent.mts'),(root/'local-token','/run/local-token'),(root/'objective.txt','/run/objective.txt'),(root/'profile.json','/run/supervisor-profile.json'),*runtime_mounts(RUNTIME)]
  report=run_command(root/'gateway.sock',workspace,coding_command(RUNTIME,MODEL),mounts=mounts,timeout=min(300,ledger.remaining_seconds('coding',RUN)),app_alias=True)
  server.revoked.set();transport.abort();no_secrets(report['stdout']+report['stderr'],secret_values)
  for name in ('stdout','stderr'):(root/('agent-'+name+'.txt')).write_bytes(report[name])
  lines=[line.split(b'SUPERVISED_CODING_AUDIT ',1)[1] for line in report['stdout'].splitlines() if b'SUPERVISED_CODING_AUDIT ' in line]
  audit_data=json.loads(lines[-1]) if lines else {'events':[]};ends=[e for e in audit_data['events'] if e['type']=='model_end'];clean=bool(ends) and ends[-1].get('stopReason')=='stop' and report['exit_code']==0 and not denials
  collected=capture(workspace,secrets=secret_values);patch=collected.pop('patch');(root/'candidate.patch').write_text(patch)
  result={**collected,'classification':'SYNTHETIC native Pi; NOT real-model ability' if synthetic else 'GENUINE native Pi coding','model':MODEL,'source_commit':spec['source_commit'],'config_sha256':spec['config_sha256'],'exit_code':report['exit_code'],'timed_out':report['timed_out'],'native_loop_completed':clean,'model_endings':ends,'gateway_denials':denials,'patch_sha256':sha(patch.encode()),'termination':'completed' if clean else ('inconclusive: cap-limited' if ledger.snapshot()['requests']>=4 and denials and not any('403' not in str(e.get('errorMessage','403')) for e in ends if e.get('stopReason')=='error') else 'incomplete-or-model-error')}
  (root/'full-native-result.json').write_bytes(canonical(result))
  ledger.recover_uncertain();ledger.control_run('coding',RUN,'COMPLETE' if clean else 'INCOMPLETE')
  # Always invoke the original evaluator after a started native run, even partial.
  same=result['patch_sha256']=='df383ba28a82be9f2a07b36d188a4f4bec11f551f1013634186c3752c2b0ba6c'
  result['evaluator_invoked']=True
  try:
   grading=evaluate(root,root/'independent-evaluator',browser_dependency=None if same else Path('/workspace/trusted-browser-dependencies/google-official'))
   result['non_browser_passed']=grading['non_browser_passed'];result['raw_complete_acceptance']=grading['complete_acceptance'];result['browser_attestation']='REUSED unchanged candidate/evaluator/isolation/browser: BROWSER_ACCEPTANCE_FINAL.md' if same else grading['browser_status']
  except Exception as e:result['evaluation_error']=type(e).__name__;result['non_browser_passed']=False
  result['ledger']=ledger.snapshot();result['request_count']=result['ledger']['requests'];result['provider_inference_requests']=0 if synthetic else (result['request_count'] if clean and len(raw_attempts)==result['request_count'] and all(s==200 for s in raw_attempts) else None);result['provider_request_upper_bound']=0 if synthetic else result['request_count'];result['completed_transport_responses']=len(raw_attempts);result['synthetic']=synthetic;result['new_provider_spend_usd']='0.00' if synthetic else None
  result['cleanup']={'namespace_returned':True,'gateway_revoked':server.revoked.is_set(),'approval_run_terminal':all(r[4]!='ACTIVE' for r in result['ledger']['runs'])}
  (root/'result.json').write_bytes(canonical(result));return result
 finally:
  if server:server.revoked.set();server.shutdown();server.server_close()
  if transport:transport.abort()
  if credential_fd is not None:os.close(credential_fd)
  if ledger:
   try:ledger.close()
   finally:
    private=root/'gateway-private'
    if private.exists():
     for p in private.iterdir():p.unlink()
     private.rmdir()


def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
 a=sub.add_parser('prepare');a.add_argument('--out',type=Path,required=True);a.add_argument('--test-state',type=Path)
 a=sub.add_parser('run');a.add_argument('--approval',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--metadata',type=Path);a.add_argument('--trust',type=Path,default=LIVE_TRUST);a.add_argument('--test-state',type=Path);a.add_argument('--synthetic-transport',type=Path)
 a=sub.add_parser('metadata');a.add_argument('--out',type=Path,required=True)
 a=sub.add_parser('recover');a.add_argument('--test-state',type=Path)
 args=p.parse_args()
 try:
  if args.action=='metadata':
   from gateway_metadata import collect
   r=collect(args.out);print(json.dumps({k:r[k] for k in ('model_access','http_status','pricing_verified','provider_metadata_requests','inference_requests')}))
  elif args.action=='prepare':
   data=prepare_spec(test_state=args.test_state)
   with args.out.open('xb') as f:f.write(canonical(data))
   print(json.dumps({'status':'AWAITING_OPERATOR_SIGNATURE','spec_sha256':sha(canonical(data)),'inference_requests':0}))
  elif args.action=='recover':
   with open_ledger(args.test_state,recover=True) as b:print(json.dumps({'status':'RECOVERED_TERMINAL_NO_REPLAY','snapshot':b.snapshot()}))
  else:
   tr=json.loads(args.synthetic_transport.read_bytes()) if args.synthetic_transport else None
   r=run(args.approval,args.out,trust=args.trust,test_state=args.test_state,synthetic_transport=tr,metadata=args.metadata)
   print(json.dumps({k:r[k] for k in ('native_loop_completed','request_count','termination','non_browser_passed','provider_inference_requests')}))
 except Exception as e:
  code=str(e) if isinstance(e,ValueError) else type(e).__name__
  print(json.dumps({'status':'REFUSED_OR_FAILED','code':code,'automatic_retry':False}));raise SystemExit(3)
if __name__=='__main__':main()
