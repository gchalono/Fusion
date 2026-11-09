"""FNXC:TaskManagerIntegration 2026-11-09-19:53:
TEST DOUBLE acceptance control, not a new frozen criterion. Observe only original
CRUD/dates/SQLite/local-web behaviors. HTTP routes are observation adapters from
common instructions, not claimed original requirements. Browser and tests pending.
Protect trusted grade state with existing no-network/seccomp namespace and private
MAC. Candidate subprocess gets no key, hidden tests or host credential variables.
"""
import ctypes
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import re
import time


def inside():
    config=json.loads(sys.stdin.read());key=bytes.fromhex(config['grading_key']);os.environ['TASK_MANAGER_NODE']=config['node']
    if ctypes.CDLL(None).prctl(4,0)!=0:raise RuntimeError('grader_dumpability_guard_failed')
    app=None;checks=[];error=None
    def start():
        process=subprocess.Popen([sys.executable,'-B','/work/application.py'],env={'PATH':os.environ['PATH'],'DATA_DIR':'/tmp/task-data','PORT':'8080'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        for _ in range(100):
            try:
                r=request('GET','/');assert r[0]==200;return process
            except Exception:
                if process.poll() is not None:break
                time.sleep(.02)
        if process.poll() is None:os.killpg(process.pid,signal.SIGKILL)
        process.wait();raise AssertionError('no working local web application')
    def stop(process):
        if process.poll() is None:os.killpg(process.pid,signal.SIGKILL)
        process.wait()
    def request(method,path,body=None):
        c=http.client.HTTPConnection('127.0.0.1',8080,timeout=2)
        try:
            c.request(method,path,None if body is None else json.dumps(body),{'Content-Type':'application/json'});r=c.getresponse();b=r.read()
            return r.status,b if path=='/' else json.loads(b) if b else None
        finally:c.close()
    try:
        app=start();page=request('GET','/')[1];assert b'<' in page and bool(page.strip());checks.append('local_web_page')
        status,t=request('POST','/api/tasks',{'title':'original task','due_date':'2027-03-17'});assert status==201 and t['title']=='original task' and t['due_date']=='2027-03-17';checks.append('create_and_due_date')
        ident=t['id'];path='/api/tasks/'+ident
        assert request('GET',path)[1]['title']=='original task';checks.append('view')
        assert request('PATCH',path,{'title':'edited task'})[1]['title']=='edited task';checks.append('edit')
        assert request('PATCH',path,{'completed':True})[1]['completed'] is True;checks.append('complete')
        stop(app);app=None
        database=Path('/tmp/task-data/tasks.sqlite3');assert database.read_bytes().startswith(b'SQLite format 3\x00')
        db=sqlite3.connect('file:'+str(database)+'?mode=ro',uri=True)
        names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        assert any(any('edited task' in str(v) for v in row) for n in names for row in db.execute('SELECT * FROM "'+n.replace('"','""')+'"'));db.close()
        app=start();assert request('GET',path)[1]['completed'] is True;checks.append('sqlite_persistence_restart')
        assert request('DELETE',path)[0]==204;assert request('GET','/api/tasks')[1]==[];checks.append('delete')
        node=os.environ['TASK_MANAGER_NODE']
        browser=subprocess.run([node,'/eval/task_manager_browser.mjs'],capture_output=True,timeout=20,env={'PATH':os.environ['PATH'],'HOME':'/tmp'})
        if browser.returncode:sys.stderr.write(browser.stderr.decode(errors='replace'))
        assert browser.returncode==0,'browser behavior failed: '+browser.stderr.decode(errors='replace')[:300]
        observation=json.loads(browser.stdout);assert observation['browser_CRUD'] and observation['external_requests']==0;checks.append('browser_CRUD')
        stop(app);app=None
        candidate_tests=subprocess.run([sys.executable,'-B','/work/application.py','--test'],capture_output=True,timeout=10,env={'PATH':os.environ['PATH'],'DATA_DIR':'/tmp/unit-data','PORT':'8080'})
        log=(candidate_tests.stdout+candidate_tests.stderr).decode(errors='replace')
        assert candidate_tests.returncode==0 and re.search(r'Ran [1-9][0-9]* test',log) and 'OK' in log,'real local test run not verified'
        assert 'unittest' in Path('/work/application.py').read_text(),'test-source evidence missing'
        checks.append('automated_tests_observed')
    except Exception as e:error=type(e).__name__+': '+str(e)
    finally:
        if app is not None:stop(app)
    record={'classification':'TEST DOUBLE ORIGINAL-OBJECTIVE CONTROL; NOT NATIVE ARM SUCCESS','success':error is None,'checks':checks,'error':error,'unverified':['general implementation interface compatibility','complete proof of arbitrary candidate test quality']}
    raw=json.dumps(record,sort_keys=True,separators=(',',':')).encode()
    print(json.dumps({'record':record,'authentication':hmac.new(key,raw,'sha256').hexdigest()}))


def grade(candidate, output):
    from execution import run_command
    from contract import canonical
    import secrets,shutil
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    # Explicit allowlist: malicious untracked tests and fabricated reports are not copied.
    raw=Path(candidate).read_bytes();checkout=output/'fresh-checkout';checkout.mkdir()
    (checkout/'application.py').write_bytes(raw)
    env={'PATH':os.defpath,'HOME':str(output)}
    for args in (['init','-q'],['add','application.py'],['-c','user.name=TEST DOUBLE','-c','user.email=double@example.invalid','commit','-qm','TEST DOUBLE isolated grading candidate']):
        subprocess.run(['git',*args],cwd=checkout,env=env,check=True,capture_output=True)
    key=secrets.token_bytes(32)
    import shutil
    playwright=Path('/workspace/Fusion/node_modules/.pnpm/playwright-core@1.60.0/node_modules/playwright-core')
    if not playwright.is_dir():raise RuntimeError('prepared_playwright_dependency_missing')
    mounts=[(Path(__file__).resolve(),'/eval/task_manager_grader.py'),(Path(__file__).with_name('task_manager_browser.mjs').resolve(),'/eval/task_manager_browser.mjs'),(playwright,'/opt/task-playwright')]
    # Node path is a public interpreter already mounted by the shared namespace.
    node=shutil.which('node')
    # Set the path in the key-bearing trusted input, not the candidate environment.
    p=run_command(None,checkout,[sys.executable,'-B','/eval/task_manager_grader.py','--inside'],mounts=mounts,timeout=45,stdin=canonical({'grading_key':key.hex(),'node':node}))
    (output/'grader-stderr.txt').write_bytes(p['stderr'])
    if p['exit_code'] or p['timed_out']:raise RuntimeError('isolated_grader_infrastructure_failed:'+p['stderr'].decode(errors='replace')[:500])
    envelope=json.loads(p['stdout']);record=envelope['record']
    if not hmac.compare_digest(envelope['authentication'],hmac.new(key,canonical(record),'sha256').hexdigest()):raise ValueError('untrusted_grade')
    (output/'partial-acceptance.json').write_bytes(canonical(record))
    return record

if __name__=='__main__':
    if sys.argv[1:]==['--inside']:inside()
    else:raise SystemExit('No live execution interface')
