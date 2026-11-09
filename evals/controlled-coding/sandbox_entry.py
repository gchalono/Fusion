"""FNXC:OfflineFinal 2026-11-09-05:40: Trusted read-only bridge/exec bootstrap.
Commands and every descendant inherit namespaces, seccomp and no_new_privs.
There is no gateway fallback and no host control interface inside the view.
"""
import sys
import threading
import subprocess
from isolation import Bridge,Relay

bridge=Bridge(('127.0.0.1',39777),Relay)
threading.Thread(target=bridge.serve_forever,daemon=True).start()
try:raise SystemExit(subprocess.run(sys.argv[1:],close_fds=True).returncode)
finally:bridge.shutdown();bridge.server_close()
