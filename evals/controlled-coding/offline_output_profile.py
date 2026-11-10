"""Current operator-authorized Experiment 2 TEST DOUBLE profile; defaults unchanged.
Not a historical approval, paid authorization, production option or Experiment 1 option.
"""
from decimal import Decimal,ROUND_CEILING
NAME='experiment2-offline-test-double-768'
TASK='phase2m-personal-task-manager'
def ceiling(data,*,offline=False,production=False,paid=False):
 if 'offline_output_profile' not in data:return 512
 if not offline or production or paid:raise ValueError('offline_profile_context_required')
 required={'experiment_id':TASK,'offline_output_profile':NAME,'offline_only':True,
 'provider_spend_authorized_usd':'0.00','model':'gpt-4.1-mini-2025-04-14','provider':'OpenAI','coding_runs':3,'coding_allocation_usd':'0.36','coding_attempts_per_run':4,'max_input_tokens':32000,
 'max_output_tokens':4096,'frozen_coding_token_limit':144384,'per_run_coding_cap_usd':'0.12',
 'planning_reserve_usd':'0.50','aggregate_cap_usd':'2.00','coding_seconds':300,'request_seconds':60,
 'input_usd_per_million':'0.40','output_usd_per_million':'1.60'}
 if any(type(data.get(k)) is not type(v) or data.get(k)!=v for k,v in required.items()):raise ValueError('offline_profile_contract_mismatch')
 if 4*(32000+768)>data['frozen_coding_token_limit']:raise ValueError('offline_profile_token_limit')
 worst=4*int((Decimal(32000)*Decimal('.40')+Decimal(768)*Decimal('1.60')).to_integral_value(rounding=ROUND_CEILING))
 if worst!=56116 or worst>120000:raise ValueError('offline_profile_budget')
 return 768
