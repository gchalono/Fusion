"""FNXC:LiveCoding 2026-11-10-06:16: Trusted gateway non-inference metadata.
Exactly one fixed authenticated model GET; no redirects/retries or credential logs.
"""
import hashlib,json,os,re,time
from html.parser import HTMLParser
from urllib.request import build_opener,HTTPRedirectHandler,Request
from urllib.error import HTTPError,URLError
MODEL='gpt-4.1-mini-2025-04-14'
DOC='https://developers.openai.com/api/docs/models/gpt-4.1-mini'
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,data):self.parts.append(data)
def collect(out):
 result={'timestamp':time.time(),'model_access':'MODEL_ACCESS_UNVERIFIED','http_status':None,'model':{},'pricing_verified':False,'documentation_url':DOC,'inference_requests':0,'provider_metadata_requests':0,'billing_or_inference_permission_proven':False}
 opener=build_opener(NoRedirect())
 try:
  with opener.open(DOC,timeout=20) as response:raw=response.read(4_000_001);status=response.status
  if len(raw)>4_000_000:raise ValueError('documentation_size_limit')
  parsed=Text();parsed.feed(raw.decode('utf8'));text=' '.join(parsed.parts);result.update(documentation_status=status,documentation_sha256=hashlib.sha256(raw).hexdigest())
  result['pricing_verified']=bool('GPT-4.1 mini' in text and re.search(r'Input\s*\$0\.40.*Cached input\s*\$0\.10.*Output\s*\$1\.60',text,re.S))
  result['documentation_observations']={'context_1047576_present':'1,047,576' in text,'output_32768_present':'32,768' in text,'chat_completions_mentioned':'Chat Completions' in text,'streaming_mentioned':'Streaming' in text,'function_calling_mentioned':'Function calling' in text,'deprecated_mentioned':'Deprecated' in text or 'deprecated' in text}
 except (OSError,ValueError,HTTPError,URLError) as error:result['documentation_status']=getattr(error,'code',None);result['documentation_error']='unreachable_or_unverified'
 key=os.environ.pop('OPENAI_API_KEY',None)
 if key:
  result['provider_metadata_requests']=1
  request=Request('https://api.openai.com/v1/models/'+MODEL,headers={'Authorization':'Bearer '+key,'Accept':'application/json'},method='GET')
  try:
   with opener.open(request,timeout=20) as response:raw=response.read(100001);result['http_status']=response.status
   if len(raw)>100000 or key.encode() in raw:raise ValueError('unsafe_metadata_response')
   data=json.loads(raw);result['model']={k:data[k] for k in ('id','object','created','owned_by') if k in data and isinstance(data[k],(str,int))}
   if result['http_status']==200 and result['model'].get('id')==MODEL:result['model_access']='VERIFIED'
  except (OSError,ValueError,HTTPError,URLError) as error:result['http_status']=getattr(error,'code',None);result['metadata_error']='authentication_model_or_network_failure'
 # Never persist headers, error bodies, key data or response fields beyond allowlist.
 with out.open('xb') as f:f.write(json.dumps(result,sort_keys=True).encode())
 return result
