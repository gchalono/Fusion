"""Non-inference readiness report. Reads config, never credential values."""
import argparse
import json
import os
import re
from gateway import Policy, Blocked


def missing_authorization(c):
    missing = []
    for key in ("provider", "model", "credential_env_var", "pilot_goal", "answerer"):
        if not isinstance(c.get(key), str) or not c[key].strip() or "<" in c[key]:
            missing.append(key)
    for key in ("max_model_calls", "max_interview_turns"):
        if type(c.get(key)) is not int or c[key] <= 0:
            missing.append(key)
    for key in ("spend_ceiling_usd", "input_price_per_million", "output_price_per_million"):
        from gateway import dollars
        try:
            dollars(c.get(key))
        except Blocked:
            missing.append(key)
    hosts = c.get("approved_hosts")
    if not isinstance(hosts, list) or not hosts or any(not isinstance(x, str) or "<" in x for x in hosts):
        missing.append("approved_hosts")
    if c.get("live_authorized") is not True:
        missing.append("paid_inference_authorization")
    return missing


def inspect(c):
    missing = missing_authorization(c)
    name = c.get("credential_env_var", "")
    if isinstance(name, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        # Presence only. Never retrieve its value.
        credential_status = "set" if name in os.environ else "unset"
    else:
        credential_status = "name_missing"
    policy_status = "not_checked"
    if not missing:
        try:
            Policy.from_config(c)
            policy_status = "valid_declaration_evidence_not_verified"
        except Blocked:
            policy_status = "invalid_or_unsupported"
    return {"status": "PILOT_BLOCKED", "missing_authorization": missing,
            "credential_presence": credential_status, "policy": policy_status,
            "remaining_engineering": ["isolated_native_driver_and_snapshots",
                                      "independently_verified_model_token_pricing_contract",
                                      "exclusive_model_egress_and_transport_credential_boundary"],
            "model_calls": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    args = parser.parse_args()
    print(json.dumps(inspect(json.load(open(args.config))), indent=2))
    raise SystemExit(2)
