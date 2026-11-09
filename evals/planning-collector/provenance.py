"""Read-only source and exact patch provenance; no inference or credential access."""
import hashlib
import json
import subprocess
import sys


def capture(source_commit):
    def git(*args):
        return subprocess.check_output(["git", *args])
    source = git("rev-parse", "--verify", source_commit + "^{commit}").decode().strip()
    collector = git("rev-parse", "HEAD").decode().strip()
    if git("status", "--porcelain").strip():
        raise RuntimeError("provenance_requires_clean_worktree")
    patch = git("diff", "--binary", "--no-ext-diff", source, collector, "--")
    protocol = open("evals/planning-collector/protocol.md", "rb").read()
    return {"source_commit": source, "collector_commit": collector,
            "patch_sha256": hashlib.sha256(patch).hexdigest(),
            "protocol_sha256": hashlib.sha256(protocol).hexdigest(),
            "rate_limit_identifier": "fusion-phase2a-pilot", "pilot_status": "PILOT_BLOCKED"}


if __name__ == "__main__":
    print(json.dumps(capture(sys.argv[1]), indent=2))
