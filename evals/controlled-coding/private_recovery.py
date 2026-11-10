"""Local-only exact-byte recovery for the 32 approved private dependencies.
No credential access, reconstruction, external destination or encryption keys.
"""
import argparse,hashlib,io,json,os,re,tarfile
from pathlib import Path

def sha(raw):return hashlib.sha256(raw).hexdigest()
def build(mapping,output,restore,*,base=Path('/workspace')):
 mapping=Path(mapping);output=Path(output);restore=Path(restore);base=Path(base).resolve()
 if output.exists() or restore.exists():raise ValueError('recovery_destination_exists')
 entries=json.loads(mapping.read_text())['private_dependencies']
 if len(entries)!=32:raise ValueError('expected_32_dependencies')
 files={};manifest=[]
 for e in entries:
  p=Path(e['source_path']);relative=p.relative_to(base)
  if p.is_symlink() or p.resolve()!=p or '..' in relative.parts:raise ValueError('unsafe_recovery_path')
  raw=p.read_bytes()
  if sha(raw)!=e['sha256']:raise ValueError('private_hash_mismatch:'+str(relative))
  if raw.startswith(b'SQLite format 3\0') or p.suffix in ('.db','.sqlite','.key','.pem') or p.name.startswith('.env'):raise ValueError('private_archive_forbidden_artifact')
  # Boundary-aware credential check; never output matched bytes.
  patterns=[rb'(?<![A-Za-z0-9])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}',rb'gh[pousr]_[A-Za-z0-9]{20,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'AKIA[A-Z0-9]{16}',rb'(?i)Bearer\s+[A-Za-z0-9._~+/-]{24,}']
  if any(re.search(x,raw) for x in patterns):raise ValueError('private_archive_secret_pattern:'+str(relative))
  name=relative.as_posix()
  if name in files:raise ValueError('duplicate_recovery_path')
  files[name]=raw;manifest.append({'relative_path':name,'sha256':e['sha256']})
 output.mkdir(mode=0o700,parents=True);restore.mkdir(mode=0o700,parents=True)
 archive=output/'private-dependencies.tar.gz'
 record={'format':1,'source_mapping_sha256':sha(mapping.read_bytes()),'root':'workspace-relative','files':manifest}
 with tarfile.open(archive,'w:gz') as t:
  for name,raw in [*files.items(),('RECOVERY_MAPPING.json',json.dumps(record,sort_keys=True).encode())]:
   info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o600;t.addfile(info,io.BytesIO(raw))
 archive.chmod(0o600)
 with tarfile.open(archive,'r:gz') as t:
  names=set()
  for member in t:
   relative=Path(member.name)
   if not member.isfile() or relative.is_absolute() or '..' in relative.parts or member.name in names:raise ValueError('unsafe_archive_member')
   names.add(member.name);raw=t.extractfile(member).read()
   if member.name!='RECOVERY_MAPPING.json' and sha(raw)!=next(x['sha256'] for x in manifest if x['relative_path']==member.name):raise ValueError('archive_hash_mismatch')
   p=restore/relative;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True);p.write_bytes(raw);p.chmod(0o600)
 if names!=set(files)|{'RECOVERY_MAPPING.json'}:raise ValueError('archive_inventory_mismatch')
 for e in manifest:
  if sha((restore/e['relative_path']).read_bytes())!=e['sha256']:raise ValueError('restored_hash_mismatch')
 result={'status':'LOCAL_PRIVATE_ARCHIVE_RESTORE_VERIFIED','files':32,'archive_sha256':sha(archive.read_bytes()),'mapping_sha256':record['source_mapping_sha256'],'off_environment_durability':'BLOCKED: no authorized protected external destination','encryption':'none: trusted local-only; permission restricted','private_recovery_verified_off_environment':False}
 (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');(output/'receipt.json').chmod(0o600);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mapping',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--restore',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.mapping,a.output,a.restore),indent=2))
