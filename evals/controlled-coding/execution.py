"""FNXC:OfflineFinal 2026-11-09-05:40:
One secured command adapter for coding and independent evaluation. Deadlines are
outside the model process. Read-only mounts are chosen only by the trusted
harness; hidden tests/approval/ledger paths never enter the coding mount list.
"""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from isolation import namespace_command
from security_filter import export_filter

ROOT=Path(__file__).resolve().parent


def run_command(socket_path, workspace, command, *, mounts=(), timeout=300, stdin=None, abort_event=None):
    with tempfile.TemporaryFile() as policy:
        export_filter(policy)
        entries=[(ROOT/'sandbox_entry.py','/eval/sandbox_entry.py'),*mounts]
        actual=[sys.executable,'-B','/eval/sandbox_entry.py',*command] if socket_path else command
        argv=namespace_command(socket_path,Path(workspace),[],seccomp_fd=policy.fileno(),command_override=actual,readonly_mounts=entries)
        env={'PATH':os.environ['PATH'],'HOME':tempfile.gettempdir()}
        process=subprocess.Popen(argv,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True,pass_fds=(policy.fileno(),),start_new_session=True)
        started=time.monotonic()
        first=True
        while True:
            aborted=abort_event is not None and abort_event.is_set()
            expired=time.monotonic()-started>=timeout
            if aborted or expired:
                # Only the owned namespace/process group; never host-wide cleanup.
                if process.poll() is None:os.killpg(process.pid,signal.SIGKILL)
                stdout,stderr=process.communicate()
                return {'exit_code':process.returncode,'stdout':stdout,'stderr':stderr,'elapsed_seconds':time.monotonic()-started,'timed_out':expired,'aborted':aborted}
            try:
                stdout,stderr=process.communicate(stdin if first else None,timeout=min(.1,max(.001,timeout-(time.monotonic()-started))))
                return {'exit_code':process.returncode,'stdout':stdout,'stderr':stderr,'elapsed_seconds':time.monotonic()-started,'timed_out':False,'aborted':False}
            except subprocess.TimeoutExpired:first=False


def runtime_mounts(runtime):
    runtime=Path(runtime).resolve()
    # Evaluation fixtures and credentials live under evals/HOME, neither mounted.
    entries=[]
    for name in ('packages','node_modules','plugins','package.json','tsconfig.json','tsconfig.base.json'):
        path=runtime/name
        if path.exists():entries.append((path,path))
    return entries


def coding_command(runtime, model):
    runtime=Path(runtime).resolve()
    node=__import__('shutil').which('node')
    return [node,'--import',str(runtime/'node_modules/tsx/dist/loader.mjs'),'/eval/coding-agent.mts',str(runtime),model,'/run/objective.txt']
