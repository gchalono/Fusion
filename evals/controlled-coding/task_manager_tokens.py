"""FNXC:TaskManagerOfflineValidation 2026-11-09-20:38:
Offline wire measurements. UTF-8/JSON byte upper bounds, never measured tokens.
B/C contexts are labeled dry projections of captured native A templates; no B/C
session or fabricated provider usage. Proposed limits are never activated here.
"""
import copy,json,hashlib,math,sqlite3
from decimal import Decimal,ROUND_CEILING
from pathlib import Path
from task_manager_adapter import experiment_contract,load_arm,sha,arming_arithmetic
from contract import canonical


def measure(native_root):
 root=Path(native_root);templates=[json.loads((root/f'native-wire-{i:02}.json').read_bytes()) for i in (1,2)]
 a=load_arm('/workspace/phase2m-genuine-success','/workspace/phase2n-evaluation/frozen','A').decode()
 for body in templates:
  texts=[part['text'] for m in body['messages'] if m['role']=='user' for part in m['content'] if part['type']=='text']
  assert texts==[a]
 d=experiment_contract();arms={}
 for arm in 'ABC':
  raw=load_arm('/workspace/phase2m-genuine-success','/workspace/phase2n-evaluation/frozen',arm);text=raw.decode();wires=[]
  for template in templates:
   body=copy.deepcopy(template)
   for m in body['messages']:
    if m['role']=='user':m['content'][0]['text']=text
   wires.append(body)
  input_bounds=[len(canonical(v)) for v in wires]
  fields={'initial_prompt_utf8_bytes_bound':len(raw),'initial_prompt_serialized_string_bytes':len(canonical(text)),
          'system_developer_message_json_bytes':len(canonical([m for m in wires[0]['messages'] if m['role'] in ('system','developer')])),
          'tool_schemas_json_bytes':len(canonical(wires[0].get('tools',[]))),
          'assistant_tool_call_message_json_bytes':len(canonical([m for m in wires[1]['messages'] if m['role']=='assistant'])),
          'tool_result_message_json_bytes':len(canonical([m for m in wires[1]['messages'] if m['role']=='tool'])),
          'initial_request_input_upper':input_bounds[0],'followup_request_context_input_upper':input_bounds[1],
          'fixture_output_reservation_per_request':512,'pricing_contract_output_max_per_request':d['max_output_tokens'],
          'fixture_cumulative_input_upper':sum(input_bounds),'fixture_two_request_cumulative_upper':sum(input_bounds)+1024,
          'contract_max_output_two_request_upper':sum(input_bounds)+2*d['max_output_tokens'],
          'reproduced_prompt_only_lower_bound':2*len(raw),'actual_model_tokens':None,
          'native_context_window':32000,'context_check_bound':max(input_bounds)+512,
          'fits_active_16000':sum(input_bounds)+1024<=16000,
          'fits_each_32000_input_request_bound':max(input_bounds)<=32000,
          'fits_native_32000_context_conservatively':max(input_bounds)+512<=32000,
          'classification':'VERIFIED captured native A fixture' if arm=='A' else 'VERIFIED dry projection; B/C not dispatched',
          'input_sha256':sha(raw),'wire_sha256':[sha(canonical(v)) for v in wires]}
  # Cost in micro-USD: input_bound * $/million + output_bound * $/million.
  price=lambda i,o:int((Decimal(i)*Decimal(d['input_usd_per_million'])+Decimal(o)*Decimal(d['output_usd_per_million'])).to_integral_value(rounding=ROUND_CEILING))
  fields['fixture_two_request_reserved_micro_usd']=sum(price(i,512) for i in input_bounds)
  fields['contract_output_two_request_reserved_micro_usd']=sum(price(i,d['max_output_tokens']) for i in input_bounds)
  fields['fits_120000_micro_run_cap']=fields['contract_output_two_request_reserved_micro_usd']<=120000
  arms[arm]=fields
 c=sqlite3.connect(root/'experiment.db')
 actual=c.execute('SELECT input_upper,output_upper FROM request_bounds ORDER BY reservation_id').fetchall();c.close()
 assert actual==[(arms['A']['initial_request_input_upper'],512),(arms['A']['followup_request_context_input_upper'],512)]
 legacy_reservations=[json.loads(p.read_bytes()) for p in root.glob('gateway-*/reservation-*.json')]
 legacy_reserved=sum(v['reserved_micro_usd'] for v in legacy_reservations)
 max_requests=d['coding_attempts_per_run'];input_max=d['max_input_tokens'];output_max=d['max_output_tokens']
 universal=max_requests*(input_max+output_max)
 worst_per=price(input_max,output_max);worst_all=worst_per*max_requests
 proposal={'status':'PROPOSED_NOT_ACTIVE','operator_approval_artifact':'none','not_an_approval':True,
           'experiment':'Experiment 2 only','existing_cumulative_bound':16000,'proposed_cumulative_bound':universal,
           'derivation':f'{max_requests} * ({input_max} input upper + {output_max} output upper)',
           'measured_two_request_fixture_minimum_for_all_arms':max(v['fixture_two_request_cumulative_upper'] for v in arms.values()),
           'alternative_current_512_profile_four_request_upper':max_requests*(input_max+512),
           'alternative_measured_fixture_two_request_upper':max(v['fixture_two_request_cumulative_upper'] for v in arms.values()),
           'scope':'smallest universal bound covering every allowed four-request trace at full existing per-request maxima, not the minimum two-request fixture',
           'four_request_worst_case_reserved_micro_usd':worst_all,'per_run_cap_micro_usd':120000,
           'unchanged_dollar_caps':{'aggregate':'2.00','planning':'0.50','per_run':'0.12'},
           'unchanged_request_cap':max_requests,'unchanged_wall_seconds':d['coding_seconds'],
           'unchanged_offline_output_limit':512,'contract_output_upper_bound_unchanged':output_max,
           'fail_closed_and_durable_reservations_unchanged':True,'actual_provider_spending_authorized_usd':'0.00',
           'activation':'Requires genuine operator-authored approval bound to this proposal hash and activation by someone other than this agent.'}
 report={'status':'VERIFIED_OFFLINE_WIRE_BOUNDS','tokenizer':{'available':False,'exact_model_tokenizer':'UNAVAILABLE; no tokenizer or encoding table installed',
           'method':'existing contract max(received UTF-8 JSON bytes, normalized UTF-8 JSON bytes); captured native A bounds verified against durable ledger',
           'not_measured_model_tokens':True},'model':'gpt-4.1-mini-2025-04-14','provider_usage':None,
           'actual_legacy_fixed_gateway_reservation_micro_usd':legacy_reserved,
           'actual_shared_aggregate_ledger_reservation_micro_usd':arms['A']['fixture_two_request_reserved_micro_usd'],
           'dual_ledger_definition':'legacy gateway reserves fixed 32000-input/512-output per request; shared ledger reserves verified actual serialized-input upper/512-output; neither amount is actual provider spend',
           'counts_definition':'sum of every reserved input upper plus reserved output upper across all requests, including retries/compaction/failures; per coding run',
           'two_request_loop_definition':'initial user/system/tools request -> assistant tool call -> actual tool result -> full follow-up context resending original input',
           'component_accounting':'component JSON sizes are descriptive and overlap container framing; full request bounds, not sums of components, drive reservations',
           'native_A_raw_evidence_root':str(root),'arms':arms,'observed_extra_retry_compaction_format_requests':0,
           'retry_compaction_worst_case':'all underlying attempts share max 4 requests; no fifth is allowed; every failed or uncertain attempt retains reservation',
           'contract_max_request_input_upper':input_max,'contract_max_request_output_upper':output_max,
           'four_request_universal_cumulative_upper':universal,'four_request_worst_case_micro_usd':worst_all,
           'worst_case_planning_plus_three_coding_micro_usd':500000+3*worst_all,
           'arming':arming_arithmetic(d),'pricing_contract_path':'evals/controlled-coding/experiment-parameters.json',
           'pricing_source_status':'operator-supplied, not independently fetched this phase','budget_binding':'active 16000 cumulative bound, not .12 dollars',
           'wall_clock':'A finished under the 90-second diagnostic watchdog (<300 contract); B/C completion times UNVERIFIED; 4*60 request deadlines=240s excludes other overhead',
           'context_reference':'native configured context 32000; supplied model context 1047576, not independently verified with a provider request',
           'actual_provider_cost_usd':'0.00'}
 return report,proposal

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--native-root',type=Path,required=True);p.add_argument('--measurements',type=Path,required=True);p.add_argument('--proposal',type=Path,required=True);a=p.parse_args();report,proposal=measure(a.native_root)
 proposal['measurements_sha256']=sha(canonical(report))
 proposal['measurement_hash_encoding']='contract.canonical sorted compact JSON UTF-8, not the indented file bytes'
 for path,value in ((a.measurements,report),(a.proposal,proposal)):
  with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
 print(json.dumps({'measurements':str(a.measurements),'proposal_sha256':sha(a.proposal.read_bytes()),'arms':{k:(v['fixture_two_request_cumulative_upper'],v['fixture_two_request_reserved_micro_usd']) for k,v in report['arms'].items()}}))
