"""Attach pdb to a running authentik Python worker via PEP 768."""

import os
import subprocess
import sys


def list_python_procs() -> list[tuple[int, int, str]]:
    out = subprocess.check_output(["ps", "-eo", "pid,ppid,command"], text=True)
    procs: list[tuple[int, int, str]] = []
    for line in out.splitlines()[1:]:
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        pid_s, ppid_s, cmd = parts
        if not pid_s.isdigit() or not ppid_s.isdigit():
            continue
        procs.append((int(pid_s), int(ppid_s), cmd))
    return procs


def find_targets() -> list[tuple[int, str]]:
    # Match any authentik Python process: dev_server / runserver via manage.py,
    # gunicorn, dramatiq, or the worker_process supervisor. Go/Rust supervisors
    # and the `uv run` / shell wrappers don't match these patterns.
    needles = (
        "manage.py",
        "manage dev_server",
        "manage runserver",
        "gunicorn",
        "dramatiq",
        "lifecycle.worker_process",
        "lifecycle/worker_process",
    )
    matches = [(p, pp, c) for p, pp, c in list_python_procs() if any(n in c for n in needles)]
    matched_pids = {p for p, _, _ in matches}
    parents_of_matches = {pp for _, pp, _ in matches if pp in matched_pids}
    # A leaf is a match that isn't itself the parent of another match — this
    # picks the dev_server reloader child or the gunicorn worker, and still
    # includes single-process workers (which trivially have no child match).
    leaves = [(p, c) for p, _, c in matches if p not in parents_of_matches]
    return leaves


def attach(pid: int) -> int:
    use_sudo = os.environ.get("SUDO") == "1"
    cmd = [sys.executable, "-m", "pdb", "-p", str(pid)]
    if use_sudo:
        cmd = ["sudo", "-E", *cmd]
    print(f"attaching pdb to pid {pid} (Ctrl-D or `quit` to detach)", file=sys.stderr)
    rc = subprocess.call(cmd)
    if rc != 0 and not use_sudo and sys.platform == "darwin":
        print(
            "\nattach failed. On macOS task_for_pid is restricted; "
            f"retry with: SUDO=1 make debug-attach PID={pid}",
            file=sys.stderr,
        )
    return rc


def main() -> int:
    env_pid = os.environ.get("PID")
    if env_pid:
        if not env_pid.isdigit():
            print(f"PID={env_pid!r} is not numeric", file=sys.stderr)
            return 2
        return attach(int(env_pid))

    targets = find_targets()
    if not targets:
        print(
            "no gunicorn/dramatiq Python workers found — is `make run-server` "
            "or `make run-worker` running?",
            file=sys.stderr,
        )
        return 1
    if len(targets) > 1:
        print("multiple worker candidates — pick one with PID=<pid>:", file=sys.stderr)
        for pid, cmd in targets:
            print(f"  {pid}\t{cmd[:120]}", file=sys.stderr)
        return 1
    return attach(targets[0][0])


if __name__ == "__main__":
    sys.exit(main())
