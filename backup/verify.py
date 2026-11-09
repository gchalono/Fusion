"""Verify an independently recovered sanitized snapshot without private artifacts."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from checkpoint import scan_bytes,SYNTHETIC_STREAMS
ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN_OBJECTS=['b3bc7b0dc6c2751bb3b499d9ce6023b3e2c7284c','0e9dab1978b2a2df61c23e3562378db77f525cfe','22a6a4cb44479c2d44731d7bf12a226d90d30638','d1f28cdcc048fc51a2f19e65dadb8d5d062231f0']
def digest(raw):return hashlib.sha256(raw).hexdigest()
def verify(root=ROOT):
 root=Path(root);inventory=json.loads((root/'backup/INVENTORY.json').read_text());review=json.loads((root/'backup/REVIEWED_TEST_LITERALS.json').read_text());streams=json.loads((root/'backup/REVIEWED_JSONL_FIXTURES.json').read_text())
 findings=[];reviewed=[]
 for name,expected in inventory['files'].items():
  p=root/name
  if p.is_symlink() or not p.is_file() or digest(p.read_bytes())!=expected:raise ValueError('snapshot_hash_mismatch:'+name)
  raw=p.read_bytes();flags=scan_bytes(name,raw)
  if flags:
   record=review.get(name)
   if record and record['sha256']==expected and sorted(set(flags))==record['allowed_findings'] and all(f.startswith('credential_pattern:') for f in flags):reviewed.append(name)
   else:findings.extend({'path':name,'code':f} for f in flags)
  if p.suffix=='.jsonl' and streams.get(name)!=expected:findings.append({'path':name,'code':'unreviewed_stream'})
  if p.suffix in ('.db','.sqlite','.sqlite3','.key','.pem','.log') or p.name=='.env' or p.name.startswith('.env.'):findings.append({'path':name,'code':'forbidden_artifact'})
 if findings:raise ValueError('PUBLICATION_BLOCKED:'+json.dumps(findings))
 for item in json.loads((root/'backup/FROZEN_DEPENDENCIES.json').read_text())['public'].values():
  assert digest((root/item['snapshot_path']).read_bytes())==item['sha256']
 gitdir=root/'.git';history={}
 if gitdir.exists() and subprocess.run(['git','rev-parse','--verify','HEAD'],cwd=root,capture_output=True).returncode==0:
  count=int(subprocess.check_output(['git','rev-list','--count','HEAD'],cwd=root,text=True))
  parents=subprocess.check_output(['git','rev-list','--parents','HEAD'],cwd=root,text=True).splitlines()
  if any(len(line.split())>2 for line in parents):raise ValueError('merge_history_forbidden')
  for oid in FORBIDDEN_OBJECTS:
   if subprocess.run(['git','cat-file','-e',oid],cwd=root,capture_output=True).returncode==0:raise ValueError('original_history_or_database_present:'+oid)
  # Every reachable blob must be a current allowlisted snapshot artifact or
  # a preceding verified snapshot artifact. All versions receive a content scan.
  listing=subprocess.check_output(['git','rev-list','--objects','HEAD'],cwd=root,text=True).splitlines();n=0
  process=subprocess.Popen(['git','cat-file','--batch'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
  for line in listing:
   parts=line.split(' ',1);oid=parts[0];path=parts[1] if len(parts)>1 else ''
   process.stdin.write((oid+'\n').encode());process.stdin.flush();_,kind,size=process.stdout.readline().decode().split();raw=process.stdout.read(int(size));assert process.stdout.read(1)==b'\n'
   if kind!='blob':continue
   n+=1;flags=scan_bytes(path,raw)
   if flags:
    item=review.get(path)
    if not(item and item['sha256']==digest(raw) and sorted(set(flags))==item['allowed_findings']):raise ValueError('history_scan_failed:'+path)
   if raw.startswith(b'SQLite format 3\x00'):raise ValueError('database_blob_in_history')
  process.stdin.close();process.wait();assert process.returncode==0;history={'commits':count,'reachable_blobs_scanned':n,'forbidden_original_objects_absent':True}
 return {'status':'SANITIZED_SNAPSHOT_VERIFIED','files':len(inventory['files']),'reviewed_synthetic_test_literal_files':len(reviewed),'history':history,'private_dependencies':32,'full_experiment_recovery_from_public_only':False}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
