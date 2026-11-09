"""Run recovered tests with original workspace and network unavailable."""
import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'evals/controlled-coding'))
from execution import run_command
with tempfile.TemporaryDirectory() as tmp:
 hosts=Path(tmp)/'hosts';hosts.write_text('127.0.0.1 localhost\n::1 localhost\n')
 r=run_command(None,ROOT,[sys.executable,'-B','/work/backup/offline_tests.py'],mounts=[(hosts,'/etc/hosts')],timeout=180)
out=r['stdout'].decode();err=r['stderr'].decode()
if r['exit_code']:print(err[-9000:],file=sys.stderr)
start=out.find('{\n  "classification"')
if start<0:
 print(out[-3000:]);print(err[-3000:]);raise SystemExit(r['exit_code'] or 1)
result=json.loads(out[start:]);result['isolation']='existing mandatory namespace + seccomp; original workspace unmounted; network isolated';result['exit_code']=r['exit_code']
(ROOT/'backup/TEST_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(r['exit_code'])
