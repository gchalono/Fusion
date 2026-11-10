"""FNXC:HistoricalLedger 2026-11-10-05:38: Read-only replay using the original
journal's strict usage/audit semantics. Standalone subprocess avoids gateway-module
collisions. No credential imports, provider traffic or historical writes.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ORIGINAL=Path('/tmp/fusion-genuine-pilot-ch9ihrxf/gateway')
EVIDENCE=Path('/workspace/phase2m-genuine-success')
MANIFEST_SHA='f6ad492d9810973d06d94bacfb6d78236fbaf038f39b7206e875daf5d7185c59'
def digest(b):return hashlib.sha256(b).hexdigest()
def replay():
 sys.path.insert(0,'/workspace/Fusion-phase2a/evals/planning-collector')
 from gateway import Policy,canonical
 from usage_reconciliation import verify_usage,strict_json
 from audit_pilot_budget import audit_fifth_pilot_budget
 raw=(EVIDENCE/'manifest.json').read_bytes()
 if digest(raw)!=MANIFEST_SHA:raise ValueError('original_manifest_mismatch')
 manifest=strict_json(raw)
 names=['config.json','run-open.json']+[f'{kind}-{i:04}.{ext}' for i in range(1,10) for kind,ext in [('reservation','json'),('request','json'),('response','raw'),('result','json'),('reconciliation','json')]]
 expected={n.removeprefix('gateway/'):v for n,v in manifest['files'].items() if n.startswith('gateway/')}
 if len(expected)!=47 or set(names)!=set(expected):raise ValueError('journal_record_count_or_order')
 actual={p.name for p in ORIGINAL.iterdir() if p.is_file()}
 if actual!=set(names) or any((ORIGINAL/n).is_symlink() for n in names):raise ValueError('journal_inventory_mismatch')
 framed=hashlib.sha256();records=[];contents={}
 for name in names:
  raw=(ORIGINAL/name).read_bytes();meta=expected[name]
  if digest(raw)!=meta['sha256'] or len(raw)!=meta['bytes']:raise ValueError('historical_record_mismatch:'+name)
  framed.update(struct.pack('>I',len(name.encode()))+name.encode()+struct.pack('>Q',len(raw))+raw)
  records.append({'name':name,'sha256':digest(raw),'bytes':len(raw)});contents[name]=raw
 cfg=strict_json(contents['config.json']);policy=Policy.from_config(cfg)
 previous=audit_fifth_pilot_budget(cfg['prior_pilot_artifacts_dir'])
 if (previous['retained_cost_micro_usd']!=cfg['prior_exposure_micro_usd'] or digest(canonical(previous))!=cfg['prior_exposure_evidence_sha256']):raise ValueError('prior_history_binding')
 opened=strict_json(contents['run-open.json'])
 if opened['prior_exposure_micro_usd']!=cfg['prior_exposure_micro_usd'] or opened['reconcile_usage'] is not True:raise ValueError('opening_balance_mismatch')
 retained=cfg['prior_exposure_micro_usd'];uncertain=0;seen=set(cfg['prior_response_ids'])
 for i in range(1,10):
  reservation=strict_json(contents[f'reservation-{i:04}.json']);record=strict_json(contents[f'result-{i:04}.json']);settlement=strict_json(contents[f'reconciliation-{i:04}.json'])
  request=contents[f'request-{i:04}.json'];response=contents[f'response-{i:04}.raw'];body=strict_json(request)
  if reservation['attempt']!=i or reservation['request_sha256']!=digest(canonical(body)):raise ValueError('historical_request_identity')
  bound=body.get('max_output_tokens',policy.output_token_bound)
  worst=(policy.input_token_bound*policy.input_price_micro_per_million+bound*policy.output_price_micro_per_million+999999)//1000000
  if type(reservation['reserved_micro_usd']) is not int or reservation['reserved_micro_usd']!=worst:raise ValueError('ambiguous_historical_amount')
  for key,bytes_,name in [('request',request,f'request-{i:04}.json'),('response',response,f'response-{i:04}.raw')]:
   if record[key]!={'file':name,'bytes':len(bytes_),'sha256':digest(bytes_)}:raise ValueError('historical_artifact_binding')
  if settlement['attempt']!=i or settlement['original_reservation_micro_usd']!=worst:raise ValueError('historical_settlement_identity')
  if settlement['status']=='settled':
   usage=verify_usage(response,record['upstream_content_type'],record['upstream_status'],policy,bound)
   if usage!=settlement['verified_usage'] or usage['response_id'] in seen:raise ValueError('historical_usage_identity')
   seen.add(usage['response_id']);cost=usage['cost_micro_usd'];retained+=cost
  elif settlement['status']=='retained' and settlement.get('verified_usage') is None:cost=worst;uncertain+=cost
  else:raise ValueError('ambiguous_historical_state')
  if (settlement['retained_cost_micro_usd']!=cost or settlement['released_micro_usd']!=worst-cost or settlement['cumulative_exposure_micro_usd']!=retained+uncertain):raise ValueError('historical_balance_mismatch')
 if retained+uncertain!=11522:raise ValueError('historical_total_mismatch')
 sha=framed.hexdigest()
 return {'schema_version':1,'journal_id':'phase2m-original-journal:'+sha,'journal_sha256':sha,'journal_bytes':sum(x['bytes'] for x in records),'record_count':47,'historical_retained_micro_usd':retained,'historical_unresolved_micro_usd':uncertain,'historical_planning_micro_usd':retained+uncertain,'records':records}
if __name__=='__main__':
 try:print(json.dumps(replay(),sort_keys=True,separators=(',',':')))
 except Exception as e:print(json.dumps({'error':type(e).__name__,'code':str(e) if isinstance(e,ValueError) else 'historical_replay_failed'}));sys.exit(3)
