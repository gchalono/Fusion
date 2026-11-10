"""FNXC:HistoricalLedger 2026-11-10-05:38: Independent recomputation; imports
NO adapter/replay/old gateway code. Strict framing/digests and raw Responses usage.
"""
import hashlib,json,struct
from pathlib import Path
from decimal import Decimal,ROUND_CEILING
r=Path('/tmp/fusion-genuine-pilot-ch9ihrxf/gateway')
def strict(raw):
 def unique(items):
  d={}
  for k,v in items:
   if k in d:raise ValueError('duplicate_key')
   d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=unique)
cfg=strict((r/'config.json').read_bytes());balance=cfg['prior_exposure_micro_usd'];sha=hashlib.sha256();size=0;count=0
order=['config.json','run-open.json']
for n in range(1,10):order.extend([f'reservation-{n:04}.json',f'request-{n:04}.json',f'response-{n:04}.raw',f'result-{n:04}.json',f'reconciliation-{n:04}.json'])
for name in order:
 raw=(r/name).read_bytes();encoded=name.encode();sha.update(len(encoded).to_bytes(4,'big'));sha.update(encoded);sha.update(len(raw).to_bytes(8,'big'));sha.update(raw);size+=len(raw);count+=1
for n in range(1,10):
 reservation=strict((r/f'reservation-{n:04}.json').read_bytes());raw=(r/f'response-{n:04}.raw').read_bytes();result=strict((r/f'result-{n:04}.json').read_bytes());reconciled=strict((r/f'reconciliation-{n:04}.json').read_bytes())
 assert hashlib.sha256(raw).hexdigest()==result['response']['sha256']
 if reconciled['status']=='retained':charge=reservation['reserved_micro_usd']
 elif reconciled['status']=='settled':
  if 'text/event-stream' in result['upstream_content_type']:
   events=[strict(x[5:].strip()) for x in raw.splitlines() if x.startswith(b'data:') and x[5:].strip()!=b'[DONE]'];term=[x for x in events if x.get('type')=='response.completed'];assert len(term)==1 and events[-1]==term[0];response=term[0]['response']
  else:response=strict(raw)
  assert response['model']==cfg['model'] and response['status']=='completed'
  u=response['usage'];cached=u['input_tokens_details']['cached_tokens'];assert u['total_tokens']==u['input_tokens']+u['output_tokens']
  cost=(Decimal(u['input_tokens']-cached)*Decimal(cfg['input_price_per_million'])+Decimal(cached)*Decimal(cfg['cached_input_price_per_million'])+Decimal(u['output_tokens'])*Decimal(cfg['output_price_per_million']))
  charge=int(cost.to_integral_value(rounding=ROUND_CEILING))
 else:raise ValueError('ambiguous_state')
 assert charge==reconciled['retained_cost_micro_usd'];balance+=charge;assert balance==reconciled['cumulative_exposure_micro_usd']
assert count==47 and balance==11522
print(json.dumps({'record_count':count,'journal_sha256':sha.hexdigest(),'journal_bytes':size,'exposure_micro_usd':balance,'independent':True},sort_keys=True))
