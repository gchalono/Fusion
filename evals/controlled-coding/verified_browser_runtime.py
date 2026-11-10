"""Read-only official dependency mapping; never relax current sandbox policy."""
import hashlib,json,stat
from pathlib import Path
PACKAGE_SHA='92148bd14dc05823a64061c2fafcf20d4d82b3fc56f5831206f16d2ac9ee3f79'
BINARY_SHA='cce8581219e59c17bcc60bff0cdfdcb2405a6d63acb1f3c32670a40814ba558c'
TREE_SHA='b8d98bc3996b64d36eb90d517797c7c2d66a05c9631e5c74bf676c5433cefec1'
DEFAULT=Path('/workspace/trusted-browser-dependencies/google-official')
def verify(root=DEFAULT):
 root=Path(root);m=json.loads((root/'verified-runtime.json').read_text());folder=root/'root/opt/google/chrome'
 if m['package_sha256']!=PACKAGE_SHA or hashlib.sha256((root/'google-chrome-stable.deb').read_bytes()).hexdigest()!=PACKAGE_SHA:raise ValueError('browser_package_identity')
 if m['binary_sha256']!=BINARY_SHA or hashlib.sha256(json.dumps(m['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()!=TREE_SHA:raise ValueError('browser_signed_tree_identity')
 if m['version']!='157.0.8103.50' or m['launch_args']!=['--single-process','--no-zygote','--no-proxy-server']:raise ValueError('browser_profile_identity')
 actual={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() or p.is_symlink()}
 if actual!=set(m['files']):raise ValueError('browser_file_inventory')
 for name,item in m['files'].items():
  if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('unsafe_browser_path')
  p=folder/name
  if item['kind']=='symlink':
   if not p.is_symlink() or str(p.readlink())!=item['target']:raise ValueError('browser_symlink_changed')
  elif bool(p.stat().st_mode&0o6000)!=item.get('privileged',False) or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256'] or p.stat().st_mode&0o222:raise ValueError('browser_dependency_changed')
 return folder,m

def mounts(root=DEFAULT):
 folder,m=verify(root);entries=[(folder,Path('/usr/lib/chromium'))]
 for name,item in m['files'].items():
  if item.get('privileged'):entries.append((Path('/dev/null'),Path('/usr/lib/chromium')/name))
 return entries,m
