import os,json,sqlite3,uuid,sys,unittest,tempfile
from http.server import BaseHTTPRequestHandler,HTTPServer
D=os.environ.get('DATA_DIR','data')
PAGE='''<!doctype html><input id="x" aria-label="Task title"><input id="d" type="date" aria-label="Due date"><button onclick="add()">Create task</button><ul id="list"></ul><script>
async function api(m,p='',v){let r=await fetch('/api/tasks'+p,{method:m,body:v&&JSON.stringify(v)});return r.status==204?null:r.json()}
async function add(){await api('POST','',{title:x.value,due_date:d.value||null});await show()}
async function show(){list.replaceChildren();for(let t of await api('GET')){let row=document.createElement('li');row.innerHTML='<span></span><button>Edit</button><button>Complete</button><button>Delete</button>';row.firstChild.textContent=t.title+' '+(t.due_date||'')+(t.completed?' completed':'');for(let [i,b] of [...row.querySelectorAll('button')].entries())b.onclick=async()=>{let v=i?null:prompt('Task title',t.title);if(i||v!==null){await api(['PATCH','PATCH','DELETE'][i],'/'+t.id,i?{completed:!t.completed}:{title:v});await show()}};list.append(row)}}show()</script>'''
def db():
 os.makedirs(D,exist_ok=True);c=sqlite3.connect(D+'/tasks.sqlite3');c.execute('create table if not exists tasks(id text primary key,v text)');return c
class H(BaseHTTPRequestHandler):
 def reply(self,n,v):
  b=v.encode() if isinstance(v,str) else json.dumps(v).encode();b=b'' if n==204 else b
  self.send_response(n);self.send_header('Content-Length',str(len(b)));self.send_header('Content-Type','text/html' if isinstance(v,str) else 'application/json');self.end_headers();self.wfile.write(b)
 def handle_task(self):
  m=self.command;p=self.path
  if p=='/' and m=='GET':return self.reply(200,PAGE)
  if not(p=='/api/tasks' or p.startswith('/api/tasks/')):return self.reply(404,{})
  i=p[11:] if p.startswith('/api/tasks/') else None
  try:
   v=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
   if not isinstance(v,dict):raise ValueError()
   if ('title' in v or m=='POST') and not(isinstance(v.get('title'),str) and v['title'].strip()):raise ValueError()
  except (ValueError,TypeError):return self.reply(400,{})
  with db() as c:
   row=c.execute('select v from tasks where id=?',(i,)).fetchone()
   if i and not row:return self.reply(404,{})
   if m=='GET':return self.reply(200,json.loads(row[0]) if i else [json.loads(r[0]) for r in c.execute('select v from tasks')])
   if m=='DELETE':c.execute('delete from tasks where id=?',(i,));return self.reply(204,{})
   if m=='POST':i=uuid.uuid4().hex;t=dict(id=i,title=v['title'],due_date=v.get('due_date'),completed=False)
   elif m=='PATCH':
    t=json.loads(row[0]);t.update({k:v[k] for k in ('title','due_date','completed') if k in v})
   else:return self.reply(405,{})
   c.execute('insert or replace into tasks values(?,?)',(i,json.dumps(t)));self.reply(201 if m=='POST' else 200,t)
 do_GET=do_POST=do_PATCH=do_DELETE=handle_task
if __name__=='__main__':
 if '--test' in sys.argv:
  class Core(unittest.TestCase):
   def test_storage(self):
    global D
    with tempfile.TemporaryDirectory() as D:
     with db() as c:c.execute("insert into tasks values('a','test')")
     with db() as c:
      self.assertEqual(c.execute('select v from tasks').fetchone()[0],'test');c.execute("update tasks set v='edited'")
      c.execute('delete from tasks')
     with db() as c:self.assertEqual(c.execute('select count(*) from tasks').fetchone()[0],0)
  unittest.main(argv=[sys.argv[0]])
 else:HTTPServer(('127.0.0.1',int(os.environ.get('PORT','8080'))),H).serve_forever()
