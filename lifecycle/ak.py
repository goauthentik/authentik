#!/ak-root/.venv/bin/python
"""Hands every command to the authentik binary.

The container runs this file as `/lifecycle/ak`.
In a development checkout, uv installs it as a console script.
"""

import os
import shutil
import sys

# Subcommands of the authentik binary
COMMANDS = ("allinone", "server", "worker", "proxy", "healthcheck", "test-all", "debug")
# Subcommands that hand their arguments to another program
PASSTHROUGH_COMMANDS = ("manage", "dump_config", "bash", "sh")


def main():
    args = sys.argv[1:]
    if args and args[0] in COMMANDS:
        argv = args
    elif args and args[0] in PASSTHROUGH_COMMANDS:
        argv = [args[0], "--", *args[1:]]
    else:
        argv = ["manage", "--", *args]

    binary = shutil.which("authentik")
    if binary:
        os.execv(binary, [binary, *argv])
    # A development checkout without an installed binary
    os.execvp("cargo", ["cargo", "run", "--", *argv])  # nosec


if __name__ == "__main__":
    main()
