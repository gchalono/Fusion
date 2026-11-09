"""FNXC:TaskManagerIntegration 2026-11-09-19:53:
Experiment 2 trusted input adapter. Preserve byte-exact historical inputs and reject
cross-task approvals. Do not dispatch a native tool loop known to exceed the inherited
16000-token upper-bound contract. No transport, credential loader or live launch API.
"""
import argparse
import hashlib
import json
from pathlib import Path
from decimal import Decimal
from contract import Contract, canonical
from budget import AggregateBudget

SOURCE = {
    'infrastructure': '73dd29ab2237fb9e7c47458b9deb0b11d681f033',
    'preparation': '40a06aa5cb932ddc0ed9bf232aca00999b355d96',
    'reconciliation': '29d027ae80795e3803ff64ddb592bc8aad0762ee',
    'merge_base': '3d92a302853c32472d2420d3835200ecc469905f',
    'integration_baseline': 'bf23a5ccbae2e7347cc533be00e38b89cef7c59a',
}
TASK = 'phase2m-personal-task-manager'
PLAN_SHA = 'f35c276d3a69484914e5581f8c1548b6f29b34449add117a87578bfae5d34456'
OBJECTIVE_SHA = '4edc93814c7a6ad5c43445ad07f853ca3350ed0e3f6dc7764e1c04e0c4cdffe0'
PREPARATION_MANIFEST_SHA = '7ff0dfdd1599f8d8864ab1f20fbcf358f21069fbb59bd27caaf330c68d7a0a3c'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def js(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()

def child(root, name):
    p = Path(name)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('unsafe_input_path')
    result = root / p
    if result.is_symlink() or not result.resolve().is_relative_to(root.resolve()):
        raise ValueError('input_path_escape')
    return result

def verify_sources(evidence, prepared):
    evidence, prepared = Path(evidence), Path(prepared)
    original = json.loads((evidence / 'manifest.json').read_bytes())
    for name, entry in original['files'].items():
        raw = child(evidence, name).read_bytes()
        if sha(raw) != entry['sha256'] or len(raw) != entry['bytes']:
            raise ValueError('historical_evidence_changed:' + name)
    manifest_raw = (prepared / 'TREATMENT_MANIFEST.json').read_bytes()
    if sha(manifest_raw) != PREPARATION_MANIFEST_SHA:
        raise ValueError('preparation_manifest_changed')
    frozen = json.loads(manifest_raw)
    if frozen['native_plan_sha256'] != PLAN_SHA or frozen['objective_sha256'] != OBJECTIVE_SHA:
        raise ValueError('wrong_task')
    if sha((evidence/'manifest.json').read_bytes()) != frozen['evidence_manifest_sha256']:
        raise ValueError('evidence_manifest_binding')
    result = json.loads((evidence/'result.json').read_bytes())
    if result['status'] != 'PILOT_SUCCESS' or result['source_commit'] != frozen['reference_production_commit']:
        raise ValueError('native_source_binding')
    transcript = json.loads((evidence/'transcript.native.json').read_bytes())
    if len(transcript) != 8:
        raise ValueError('historical_answer_count')
    audit = []
    previous = '0' * 64
    raw = (evidence/'results/human/audit.jsonl').read_bytes()
    if not raw.endswith(b'\n'):
        raise ValueError('torn_historical_audit')
    for i, line in enumerate(raw.splitlines(), 1):
        record = json.loads(line); tag = record.pop('hash')
        if record['sequence'] != i or record['previous'] != previous or sha(js(record)) != tag:
            raise ValueError('historical_audit_chain')
        previous = tag; audit.append(record)
    questions = [e['data'] for e in audit if e['type'] == 'question_exported']
    if len(questions) != 8:
        raise ValueError('question_count')
    bindings = []
    for i, (row, q) in enumerate(zip(transcript, questions), 1):
        identity = {k:q[k] for k in ('session_id', 'ordinal', 'question')}
        qhash = sha(js(identity))
        answer_file = evidence/f'human-answer-{i:03}.json'
        provenance_file = evidence/f'human-approval-provenance-{i:03}.json'
        answer = json.loads(answer_file.read_bytes()); approval = json.loads(provenance_file.read_bytes())
        command_file = evidence/f'results/human/command-{qhash}.json'
        command = json.loads(command_file.read_bytes())
        if not (row['submitted'] and row['source'] == 'explicit-human-approval'
                and q['question'] == row['question'] and qhash == row['question_sha256'] == approval['question_sha256']
                and answer == row['submitted_answer'] == approval['approved_answer']
                and approval['approval_id'] == row['approval_id'] == command['approval_id']
                and command['session_id'] == q['session_id'] and command['question_sha256'] == qhash
                and command['approved'] is True and command['action'] == 'resume' and command['answer'] == answer
                and approval['source'] == f'explicit user chat message for Phase 2M q{i}'):
            raise ValueError('historical_approval_binding')
        bindings.append({'question_identity_sha256':qhash, 'answer_file':str(answer_file),
                         'answer_sha256':sha(answer_file.read_bytes()),
                         'approval_provenance_file':str(provenance_file),
                         'approval_provenance_sha256':sha(provenance_file.read_bytes()),
                         'approval_command_file':str(command_file),'approval_command_sha256':sha(command_file.read_bytes()),
                         'source':'VERIFIED historical Phase 2M chat approval; not live authority'})
    for arm, spec in frozen['arms'].items():
        raw = child(prepared, spec['prompt_file']).read_bytes()
        if sha(raw) != spec['prompt_sha256'] or len(raw) != spec['prompt_bytes']:
            raise ValueError('frozen_prompt_changed')
        expected = ['standardized_instructions', 'objective'] + (['native_plan'] if arm != 'A' else [])
        if arm == 'C': expected += [f'human_answer_{i:03}' for i in range(1,9)]
        if [s['name'] for s in spec['segments']] != expected:
            raise ValueError('cross_arm_contamination')
        for segment in spec['segments']:
            part = raw[segment['offset']:segment['offset']+segment['bytes']]
            if sha(part) != segment['sha256']:
                raise ValueError('segment_changed')
            name=segment['name']
            if name == 'native_plan' and part != (evidence/'MissionPlanSummary.native.json').read_bytes():
                raise ValueError('native_plan_changed')
            if name.startswith('human_answer_'):
                index=int(name.rsplit('_',1)[1])
                if part != (evidence/f'human-answer-{index:03}.json').read_bytes():
                    raise ValueError('answer_bytes_changed')
            if name == 'objective' and sha(part) != OBJECTIVE_SHA:
                raise ValueError('objective_changed')
    return frozen, bindings

def experiment_contract():
    # Separate identity and database; never migrate or combine Experiment 1 ledgers.
    d = dict(Contract().data)
    if (d['aggregate_cap_usd'],d['planning_reserve_usd'],d['per_run_coding_cap_usd']) != ('2.00','0.50','0.12'):
        raise ValueError('authoritative_offline_contract_mismatch')
    d.update(experiment_id=TASK, coding_runs=3, coding_allocation_usd='0.36',
             unallocated_headroom_usd='1.14', planning_run_ids=[TASK],
             coding_run_ids=[TASK+':'+a for a in 'ABC'], frozen_coding_token_limit=16000,
             provider_spend_authorized_usd='0.00')
    return d

def arming_arithmetic(d):
    allocated=Decimal(d['planning_reserve_usd'])+d['coding_runs']*Decimal(d['per_run_coding_cap_usd'])
    threshold=Decimal('0.8')*Decimal(d['aggregate_cap_usd'])
    return {'allocated_usd':str(allocated),'threshold_usd':str(threshold),'passes':allocated<=threshold,
            'authority':'OFFLINE ONLY; provider spending remains $0.00'}

def loop_feasibility(prompt, d):
    # Pi must request again after a tool result. Both requests preserve the user
    # input. This is a lower bound on the existing conservative BYTE reservation,
    # not a claim that UTF-8 byte count equals actual tokenizer output.
    lower_bound = 2*len(prompt)
    return {'minimum_requests_for_tool_loop':2,'prompt_only_reserved_input_lower_bound':lower_bound,
            'inherited_total_token_upper_cap':d['frozen_coding_token_limit'],
            'status':'BLOCKED' if lower_bound>d['frozen_coding_token_limit'] else 'UNVERIFIED',
            'reason':'native tool-loop reservation cannot fit unchanged inputs' if lower_bound>d['frozen_coding_token_limit'] else 'runtime/tool/schema/output overhead not yet measured'}

def load_arm(evidence, prepared, arm, *, task_id=TASK):
    if task_id != TASK or arm not in ('A','B','C'):
        raise ValueError('experiment_task_or_arm_mismatch')
    frozen,_=verify_sources(evidence,prepared)
    return child(Path(prepared),frozen['arms'][arm]['prompt_file']).read_bytes()

def write_manifest(evidence,prepared,out):
    frozen, bindings=verify_sources(evidence,prepared); d=experiment_contract()
    artifact_names=['manifest.json','MissionPlanSummary.native.json','transcript.native.json',
                    'frozen-hashes.json','result.json','results/human/audit.jsonl']
    inputs={str(Path(evidence)/n):sha((Path(evidence)/n).read_bytes()) for n in artifact_names}
    for b in bindings: inputs[b['answer_file']]=b['answer_sha256'];inputs[b['approval_provenance_file']]=b['approval_provenance_sha256']
    for b in bindings:inputs[b['approval_command_file']]=b['approval_command_sha256']
    objective_file=Path(prepared)/'inputs/objective.txt'
    if sha(objective_file.read_bytes())!=OBJECTIVE_SHA:raise ValueError('objective_copy_changed')
    inputs[str(objective_file)]=OBJECTIVE_SHA
    common_file=Path('/workspace/Fusion-phase2a/evals/implementation-evaluation/COMMON_INSTRUCTIONS.md')
    if sha(common_file.read_bytes())!=frozen['common_instructions_sha256']:raise ValueError('common_instructions_changed')
    inputs[str(common_file)]=frozen['common_instructions_sha256']
    arms={}
    for a,s in frozen['arms'].items():
        file=child(Path(prepared),s['prompt_file']);inputs[str(file)]=sha(file.read_bytes())
        arms[a]={'input_file':str(file),'input_sha256':s['prompt_sha256'],'segments':s['segments'],
                 'native_tool_loop_feasibility':loop_feasibility(file.read_bytes(),d),
                 'integration_status':'NOT_RUN','classification':'TEST DOUBLE ONLY; not model performance'}
    report={'classification':'VERIFIED SOURCE MANIFEST; OFFLINE INTEGRATION BLOCKED',
            'experiment_id':TASK,'separate_from':'Experiment 1: three frozen Python tasks',
            'source_commits':SOURCE,'frozen_preparation_manifest':str(Path(prepared)/'TREATMENT_MANIFEST.json'),
            'frozen_preparation_manifest_sha256':PREPARATION_MANIFEST_SHA,'inputs':inputs,'approval_bindings':bindings,
            'arms':arms,'model_settings':{'model':d['model'],'temperature':0,'fallback':False,
             'existing_offline_double_max_output_tokens':512,'contract_output_upper_bound':4096,
             'max_requests':4,'total_reserved_token_upper_bound':16000,'wall_seconds':300},
            'environment':{'namespace':'existing execution.run_command / security_filter.export_filter',
             'tools':['read','write','bash'],'MCP':False,'writable_mount':'/work; frozen prompt expects /app (unadapted)',
             'grading':'same original-objective criteria required for all arms; reference-specific interface adapter only'},
            'budget_config':d,'budget_config_sha256':sha(canonical(d)),
            'arming':arming_arithmetic(d),'execution_order':frozen['diagnostic_execution_order'],
            'grading_status':'FAILED reference browser control; complete original-objective grading UNVERIFIED',
            'provider_spending_usd':'0.00','coding_agents_started':0,'actual_model_requests':0}
    with Path(out).open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--prepared',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
    print(json.dumps({'status':write_manifest(a.evidence,a.prepared,a.manifest)['classification'],'provider_spending_usd':'0.00'}))
