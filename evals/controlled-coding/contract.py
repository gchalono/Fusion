"""FNXC:OfflineFinal 2026-11-09-05:40:
Use operator-supplied prices only. Byte length bounds input; uncached input and
clamped output reserve worst case, rounded upward to micro-USD. Unknown features
fail closed. Test fixtures are not live authorization. Keep the 80% arming gate.
"""
import hashlib
import json
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

PARAMETERS=Path(__file__).with_name('experiment-parameters.json')


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def micro(value):
    return int((Decimal(str(value))*1000000).to_integral_value(rounding=ROUND_CEILING))


class Contract:
    def __init__(self, path=PARAMETERS):
        self.data=json.loads(Path(path).read_text());self.sha256=hashlib.sha256(canonical(self.data)).hexdigest()
        for name in ('model','provider','pricing_source','pricing_verification_date','input_usd_per_million','cached_input_usd_per_million','output_usd_per_million'):
            if not self.data.get(name):raise ValueError('missing_contract:'+name)
        for name in ('input_usd_per_million','cached_input_usd_per_million','output_usd_per_million'):
            if not Decimal(self.data[name]).is_finite() or Decimal(self.data[name])<0:raise ValueError('invalid_rate')

    def arming_errors(self):
        d=self.data;errors=[]
        allocation=Decimal(d['per_run_coding_cap_usd'])*d['coding_runs']+Decimal(d['planning_reserve_usd'])
        if allocation>Decimal(d['aggregate_cap_usd'])*Decimal('0.8'):errors.append('ARMING_ALLOCATION_EXCEEDS_80_PERCENT')
        if d.get('model_availability')!='VERIFIED':errors.append('MODEL_AVAILABILITY_UNVERIFIED')
        if Decimal(d['provider_spend_authorized_usd'])<=0:errors.append('NO_PAID_AUTHORIZATION')
        return errors

    def prepare(self, raw):
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError('duplicate_key')
                result[key]=value
            return result
        body=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite')))
        allowed={'model','messages','tools','tool_choice','parallel_tool_calls','stream','stream_options','max_tokens','max_completion_tokens','temperature','top_p','seed','store'}
        if not isinstance(body,dict) or set(body)-allowed or body.get('model')!=self.data['model']:
            raise ValueError('unknown_model_or_unpriced_feature')
        if body.get('store',False):raise ValueError('store_not_authorized')
        if not isinstance(body.get('messages'),list) or not body['messages']:raise ValueError('messages_required')
        for message in body['messages']:
            if not isinstance(message,dict):raise ValueError('invalid_message')
            content=message.get('content')
            if content is not None and not isinstance(content,str):
                if not isinstance(content,list) or any(not isinstance(p,dict) or set(p)!={'type','text'} or p['type']!='text' or not isinstance(p['text'],str) for p in content):
                    raise ValueError('unpriced_modality')
        if 'tools' in body and any(not isinstance(t,dict) or t.get('type')!='function' or set(t)!={'type','function'} for t in body['tools']):
            raise ValueError('unpriced_tool')
        fields=[k for k in ('max_tokens','max_completion_tokens') if k in body]
        if len(fields)>1:raise ValueError('ambiguous_output_limit')
        requested=body.get(fields[0],self.data['max_output_tokens']) if fields else self.data['max_output_tokens']
        if type(requested) is not int or requested<=0:raise ValueError('invalid_output_limit')
        if fields:body.pop(fields[0])
        body['max_tokens']=min(requested,self.data['max_output_tokens'])
        normalized=canonical(body)
        # Bound both received bytes and the forwarded body, never truncate input.
        bound=max(len(raw),len(normalized))
        if bound>self.data['max_input_tokens']:raise ValueError('input_byte_bound_exceeded')
        cost=(Decimal(bound)*Decimal(self.data['input_usd_per_million'])+Decimal(body['max_tokens'])*Decimal(self.data['output_usd_per_million']))
        exposure=int(cost.to_integral_value(rounding=ROUND_CEILING))
        return normalized,{'input_token_upper_bound':bound,'output_token_upper_bound':body['max_tokens'],'reserved_micro_usd':exposure,'requested_output_tokens':requested,'contract_sha256':self.sha256}

    def estimate(self, usage):
        p=usage.get('prompt_tokens');o=usage.get('completion_tokens')
        c=usage.get('prompt_tokens_details',{}).get('cached_tokens',0)
        if any(type(v) is not int or v<0 for v in (p,o,c)) or c>p:raise ValueError('invalid_usage')
        value=Decimal(p-c)*Decimal(self.data['input_usd_per_million'])+Decimal(c)*Decimal(self.data['cached_input_usd_per_million'])+Decimal(o)*Decimal(self.data['output_usd_per_million'])
        return int(value.to_integral_value(rounding=ROUND_CEILING))
