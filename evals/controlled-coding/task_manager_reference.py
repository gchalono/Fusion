"""FNXC:TaskManagerIntegration 2026-11-09-19:53:
TEST DOUBLE reference control, never a genuine model implementation or treatment.
SQLite/local HTTP/vanilla browser UI supplies original-objective core behaviors.
"""
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PAGE='''<!doctype html><title>Personal tasks</title><h1>Tasks</h1><input id="title" aria-label="Task title"><input id="due" type="date" aria-label="Due date"><button onclick="createTask()">Create task</button><ul id="tasks"></ul><script>
async function api(method,path='',data){let r=await fetch('/api/tasks'+path,{method,headers:{'Content-Type':'application/json'},body:data===undefined?undefined:JSON.stringify(data)});return r.status===204?null:r.json()}
async function createTask(){await api('POST','',{title:document.getElementById('title').value,due_date:document.getElementById('due').value||null});await show()}
async function show(){let list=document.getElementById('tasks');list.replaceChildren();for(let t of await api('GET')){let row=document.createElement('li'),name=document.createElement('span');name.textContent=t.title+' '+(t.due_date||'')+(t.completed?' completed':'');row.append(name);for(let [label,action] of [['Edit',async()=>{let title=prompt('Task title',t.title);if(title!==null)await api('PATCH','/'+t.id,{title})}],['Complete',()=>api('PATCH','/'+t.id,{completed:!t.completed})],['Delete',()=>api('DELETE','/'+t.id)]]){let b=document.createElement('button');b.textContent=label;b.onclick=async()=>{await action();await show()};row.append(b)}list.append(row)}}show();</script>'''

def connect():
    root=Path(os.environ['DATA_DIR']);root.mkdir(exist_ok=True)
    db=sqlite3.connect(root/'tasks.sqlite3');db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,title TEXT,due_date TEXT,completed INTEGER)')
    return db

def task(row):
    d=dict(row);d['completed']=bool(d['completed']);return d

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,code,obj):
        raw=b'' if code==204 else obj.encode() if isinstance(obj,str) else json.dumps(obj).encode()
        self.send_response(code);self.send_header('Content-Type','text/html' if isinstance(obj,str) else 'application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def handle_request(self):
        import uuid
        if self.command=='GET' and self.path=='/':self.send(200,PAGE);return
        parts=self.path.split('/');ident=parts[3] if len(parts)==4 else None
        if parts[1:3]!=['api','tasks']:self.send(404,{});return
        body=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
        with connect() as db:
            if self.command=='GET':
                rows=db.execute('SELECT * FROM tasks'+(' WHERE id=?' if ident else ''),(ident,) if ident else ()).fetchall()
                self.send(404 if ident and not rows else 200,task(rows[0]) if ident and rows else [task(r) for r in rows]);return
            if self.command=='POST':
                ident=uuid.uuid4().hex;db.execute('INSERT INTO tasks VALUES(?,?,?,0)',(ident,body['title'],body.get('due_date')))
            elif self.command=='PATCH':
                for k in ('title','due_date','completed'):
                    if k in body:db.execute('UPDATE tasks SET '+k+'=? WHERE id=?',(body[k],ident))
            elif self.command=='DELETE':db.execute('DELETE FROM tasks WHERE id=?',(ident,));self.send(204,{});return
            self.send(201 if self.command=='POST' else 200,task(db.execute('SELECT * FROM tasks WHERE id=?',(ident,)).fetchone()))
    do_GET=handle_request
    do_POST=handle_request
    do_PATCH=handle_request
    do_DELETE=handle_request

def tests():
    import unittest,tempfile,threading,http.client
    class Core(unittest.TestCase):
        def test_core_operations(self):
            with tempfile.TemporaryDirectory() as directory:
                os.environ['DATA_DIR']=directory
                server=HTTPServer(('127.0.0.1',0),Handler)
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                def call(method,path,body=None):
                    c=http.client.HTTPConnection('127.0.0.1',server.server_port)
                    try:
                        c.request(method,path,None if body is None else json.dumps(body));r=c.getresponse();raw=r.read();return r.status,json.loads(raw) if raw else None
                    finally:c.close()
                try:
                    code,t=call('POST','/api/tasks',{'title':'unit task','due_date':'2027-01-01'});self.assertEqual(code,201)
                    path='/api/tasks/'+t['id'];self.assertEqual(call('GET',path)[1]['due_date'],'2027-01-01')
                    self.assertEqual(call('PATCH',path,{'title':'edited','completed':True})[1]['title'],'edited')
                    self.assertTrue(call('GET',path)[1]['completed'])
                    with connect() as db:self.assertEqual(db.execute('SELECT title FROM tasks').fetchone()[0],'edited')
                    self.assertEqual(call('DELETE',path)[0],204);self.assertEqual(call('GET','/api/tasks')[1],[])
                finally:server.shutdown();server.server_close();thread.join()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Core)
    result=unittest.TextTestRunner().run(suite)
    raise SystemExit(not result.wasSuccessful())

if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--test']:tests()
    else:HTTPServer(('127.0.0.1',int(os.environ['PORT'])),Handler).serve_forever()
