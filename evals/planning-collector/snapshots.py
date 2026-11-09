"""Pure comparisons for disposable-state evidence; never reads credentials."""


def database_diff(before, after):
    keys = set(before['counts']) | set(after['counts'])
    changes = {k: [before['counts'].get(k), after['counts'].get(k)] for k in keys
               if before['counts'].get(k) != after['counts'].get(k)}
    changed_rows = sorted(k for k in keys if before['row_hashes'].get(k) != after['row_hashes'].get(k))
    return {'count_changes': changes, 'changed_rows': changed_rows,
            'forbidden': [k for k in changed_rows if k != 'project.ai_sessions']}


def filesystem_diff(before, after):
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    prefixes = ('database/', 'results/', 'scratch/gateway-artifacts/', 'scratch/jiti/', 'scratch/tsx-')
    exact = {'go', 'settled', 'home/.fusion/agent/models-store.json'}
    return {'changed': changed, 'unexpected': [k for k in changed
            if k not in exact and not k.startswith(prefixes) and not (k + '/').startswith(prefixes)]}


def process_diff(before, after):
    def records(lines):
        return {line.split()[0]: line.split()[2] for line in lines[1:] if len(line.split()) == 3}
    a, b = records(before), records(after)
    new = {pid: name for pid, name in b.items() if pid not in a and name != 'ps'}
    # PostgreSQL can lazily start an additional connection/backend process.
    return {'new': new, 'unexpected': {pid:name for pid,name in new.items() if name != 'postgres'}}
