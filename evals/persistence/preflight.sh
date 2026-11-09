#!/bin/sh
# FNXC:Persistence 2026-11-09-04:02: Read-only recovery checks; only remote refs may be fetched.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$script_dir/../.."
exec python3 -B "$script_dir/tooling.py" preflight "$@"
