"""FNXC:RealModelReadiness 2026-11-10-04:59:
Operator-requested 4096-output LOCAL rehearsal, never paid authorization.
Existing 512 defaults and historical 768 profile remain separate and unchanged.
"""
NAME = 'phase3-local-real-shape-4096'


def ceiling(data, *, offline=False, production=False, paid=False):
    from offline_output_profile import ceiling as previous
    if 'readiness_profile' not in data:
        return previous(data, offline=offline, production=production, paid=paid)
    if not offline or production or paid or 'offline_output_profile' in data:
        raise ValueError('readiness_profile_local_only')
    from task_manager_token_revision import offline_contract
    expected = offline_contract()
    expected['readiness_profile'] = NAME
    if data != expected:
        raise ValueError('readiness_profile_contract_mismatch')
    return 4096
