"""Development entrypoint for `ak`, installed by uv as a console script.

In a container this module is not used: `/lifecycle/ak` is a symlink to the
compiled `authentik` binary, which recognizes the `ak` program name and runs its
`boot` subcommand. See `src/boot.rs`.

In a development checkout there may be no compiled binary, so:

  * server, worker, allinone and healthcheck go through `cargo run -- boot`
  * dump_config goes straight to the config loader, which does not boot Django
  * every other command is a Django management command and runs without waiting for a Rust build
"""

import os
import shutil
import subprocess  # nosec
import sys

NATIVE_COMMANDS = ("server", "worker", "allinone", "healthcheck")


def main():
    """Dispatch an `ak` invocation."""
    args = sys.argv[1:]

    binary = shutil.which("authentik")
    if binary:
        os.execv(binary, [binary, "boot", *args])

    if args and args[0] in NATIVE_COMMANDS:
        os.execvp("cargo", ["cargo", "run", "--", "boot", *args])  # nosec

    if args and args[0] == "dump_config":
        os.execv(sys.executable, [sys.executable, "-m", "authentik.lib.config", *args[1:]])

    subprocess.run([sys.executable, "-m", "lifecycle.wait_for_db"], check=True)  # nosec
    os.execv(sys.executable, [sys.executable, "-m", "manage", *args])


if __name__ == "__main__":
    main()
