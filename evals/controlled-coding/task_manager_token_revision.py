"""Operator-directed Experiment 2 OFFLINE token revision; no live authorization.
Authorization source: current operator instruction, section 7:
"Activate the scoped token-bound revision after verification."
This records execution of that directive, not a fabricated signed approval.
Original proposal, frozen inputs, Experiment 1 and default contract stay unchanged.
"""
import hashlib,json
from pathlib import Path
from decimal import Decimal,ROUND_CEILING
from task_manager_adapter import experiment_contract
PROPOSAL_SHA='929ee7ad2952ab650ba8a70c0074a25d4c1c1cb25e5975324ab4600639951c9b'
def offline_contract(proposal=None):
 p=Path(proposal) if proposal else Path(__file__).with_name('TOKEN_BOUND_PROPOSED_NOT_ACTIVE.json')
 raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=PROPOSAL_SHA:raise ValueError('token_proposal_hash_mismatch')
 v=json.loads(raw);d=experiment_contract()
 assert v['experiment']=='Experiment 2 only' and v['proposed_cumulative_bound']==144384
 assert v['unchanged_request_cap']==d['coding_attempts_per_run']==4 and d['max_input_tokens']==32000 and d['max_output_tokens']==4096
 worst=int((Decimal(4)*(Decimal(32000)*Decimal(d['input_usd_per_million'])+Decimal(4096)*Decimal(d['output_usd_per_million']))).to_integral_value(rounding=ROUND_CEILING))
 if worst!=77415 or worst>int(Decimal(d['per_run_coding_cap_usd'])*1000000):raise ValueError('token_revision_budget_unsafe')
 # The ledger rounds EACH request upward: 19,354 micro-USD * 4.
 rounded=4*int((Decimal(32000)*Decimal(d['input_usd_per_million'])+Decimal(4096)*Decimal(d['output_usd_per_million'])).to_integral_value(rounding=ROUND_CEILING))
 assert rounded==77416 and rounded<=120000
 d.update(frozen_coding_token_limit=144384,offline_token_revision_proposal_sha256=PROPOSAL_SHA,offline_only=True)
 assert d['provider_spend_authorized_usd']=='0.00'
 return d
