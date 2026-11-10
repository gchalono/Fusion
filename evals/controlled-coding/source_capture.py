"""FNXC:LiveCoding 2026-11-10-06:16: Capture common TEXT source formats;
SQLite is hashed runtime data, never source. No host Git on untrusted configuration.
"""
import hashlib,os,re,stat
from pathlib import Path
from task_manager_native import new_file_patch
EXTENSIONS={'.py','.js','.mjs','.json','.sql','.html','.css','.md','.sh','.txt'}
PROHIBITED={'.fusion','.kb','.aws','.ssh','.config','node_modules','__pycache__','.venv'}
MAX_SOURCE=1_000_000;MAX_RUNTIME=8_000_000;MAX_TOTAL=8_000_000

def no_secrets(raw,secrets):
 if any(s and s.encode() in raw for s in secrets):raise ValueError('secret_in_collected_evidence')

def capture(workspace,*,secrets=()):
 root=Path(workspace);files={};modes={};runtime=[];patch='';total=0;count=0
 for directory,dirs,names in os.walk(root,followlinks=False):
  dirs.sort();names.sort()
  for name in [*dirs,*names]:
   p=Path(directory)/name;rel=p.relative_to(root);st=p.lstat()
   if stat.S_ISLNK(st.st_mode):raise ValueError('candidate_symlink')
   if rel.parts==('.git',):
    if name in dirs:dirs.remove(name)
    continue
   if any(x in PROHIBITED or x.startswith('.env') for x in rel.parts):raise ValueError('prohibited_candidate_path')
   if len(str(rel))>240 or len(rel.parts)>16 or not re.fullmatch(r'[A-Za-z0-9_./-]+',str(rel)) or '..' in rel.parts:raise ValueError('unsafe_candidate_path')
   if stat.S_ISDIR(st.st_mode):continue
   count+=1
   if count>256 or not stat.S_ISREG(st.st_mode) or st.st_nlink!=1 or st.st_mode&0o6000:raise ValueError('unsafe_candidate_file')
   if st.st_size>MAX_RUNTIME:raise ValueError('candidate_too_large')
   total+=st.st_size
   if total>MAX_TOTAL:raise ValueError('candidate_total_size')
   with p.open('rb') as f:header=f.read(16)
   if header==b'SQLite format 3\x00':
    data=p.read_bytes();no_secrets(data,secrets);runtime.append({'path':str(rel),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'classification':'runtime SQLite; excluded from source patch'});continue
   if st.st_size>MAX_SOURCE or p.suffix not in EXTENSIONS and str(rel) not in ('run-app','run-tests'):raise ValueError('unsupported_or_oversized_candidate_source')
   data=p.read_bytes()
   no_secrets(data,secrets)
   if b'\x00' in data:raise ValueError('binary_source_not_allowed')
   data.decode('utf8');mode='100755' if st.st_mode&0o111 else '100644';files[str(rel)]=hashlib.sha256(data).hexdigest();modes[str(rel)]=mode;patch+=new_file_patch(str(rel),data,mode)
 return {'candidate_files':files,'candidate_modes':modes,'runtime_data':runtime,'patch':patch}
