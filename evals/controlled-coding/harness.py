"""FNXC:ControlledCoding 2026-11-09-03:50:
Freeze objectives, starting code and independent tests before inference. Keep
missing native plans and human approvals explicit; never fabricate observations.
A/B/C share coding limits. B versus C identifies only transcript presentation.
No live transport or credential loading is exposed until gateway-only execution,
human approval and aggregate reservations can be verified.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 20261109
SETTINGS = {'model': 'gpt-4.1-mini-2025-04-14', 'temperature': 0,
            'max_output_tokens': 4096, 'max_api_requests': 4,
            'coding_token_limit': 16000, 'coding_spend_limit_usd': '0.15'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory():
    files = {}
    for path in sorted((ROOT / 'fixtures').rglob('*')):
        if path.is_symlink():
            raise ValueError('symlink_in_fixture')
        if path.is_file() and '__pycache__' not in path.parts:
            files[str(path.relative_to(ROOT))] = sha(path.read_bytes())
    return files


def manifest():
    tasks = sorted(p.name for p in (ROOT / 'fixtures').iterdir() if p.is_dir())
    order = [{'task_id': t, 'configuration': arm} for t in tasks for arm in 'ABC']
    random.Random(SEED).shuffle(order)
    return {'schema_version': 1, 'seed': SEED, 'settings': SETTINGS,
            'aggregate_new_provider_spend_limit_usd': '2.00',
            'files': inventory(), 'execution_order': order}


def verify():
    saved = json.loads((ROOT / 'frozen.json').read_text())
    if saved != manifest():
        raise ValueError('frozen_inputs_changed')
    return saved


def inputs(task, arm, plan=None):
    objective = (ROOT / 'fixtures' / task / 'objective.txt').read_text()
    result = {'objective': objective}
    if arm in 'BC':
        if plan is None:
            return None
        # Plan import requires native provenance and a separate approval artifact;
        # not even a dry run substitutes scripted answers for human approvals.
        result['native_plan'] = plan['native_plan']
    if arm == 'C':
        result['approved_clarification_answers'] = plan['approved_clarification_answers']
    return result


def dry_run(destination):
    frozen = verify()
    destination.mkdir(parents=True, exist_ok=False)
    rows = []
    for ordinal, spec in enumerate(frozen['execution_order']):
        run = destination / f"{ordinal:02}-{spec['task_id']}-{spec['configuration']}"
        run.mkdir()
        payload = inputs(spec['task_id'], spec['configuration'])
        (run / 'input.json').write_text(json.dumps(payload, indent=2)+'\n')
        # No inference and no acceptance execution is represented as a result.
        row = dict(spec, settings=SETTINGS, completion_status='not_executed',
                   blocker='live_supervisor_unavailable' if payload else 'native_plan_and_approvals_missing',
                   acceptance_passed=None, acceptance_failed=None, execution_seconds=None,
                   api_requests=None, input_tokens=None, cached_input_tokens=None,
                   output_tokens=None, coding_cost_usd=None, planning_cost_usd=None,
                   total_cost_usd=None, measured_provider_charge_usd=None,
                   human_interventions=None, errors=None, retries=None, final_diff=None,
                   artifact_location=run.name, input_sha256=sha((run/'input.json').read_bytes()))
        rows.append(row)
    result = {'status': 'offline_dry_run_only', 'frozen_manifest_sha256': sha((ROOT/'frozen.json').read_bytes()),
              'new_provider_requests_dispatched': 0, 'runs': rows}
    (destination/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['freeze', 'verify', 'dry-run', 'live'])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'freeze':
        with (ROOT/'frozen.json').open('x') as f:
            json.dump(manifest(), f, indent=2)
            f.write('\n')
    elif args.command == 'verify':
        verify()
    elif args.command == 'dry-run':
        if not args.output:
            parser.error('--output required')
        dry_run(args.output)
    else:
        parser.error('LIVE_BLOCKED: missing Phase 2M evidence, coding supervisor, sole-egress proof and explicit paid approval')


if __name__ == '__main__':
    main()
