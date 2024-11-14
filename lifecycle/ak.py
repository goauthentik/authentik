"""Wrapper for lifecycle/ak, to be installed by poetry"""

from os import WEXITSTATUS, system
from pathlib import Path
from sys import argv, exit


def main():
    """Wrapper around ak bash script"""
    current_path = Path(__file__)
    args = " ".join(argv[1:])
    res = system(f"{current_path.parent}/ak {args}")  # nosec
    exit_code = WEXITSTATUS(res)
    exit(exit_code)


if __name__ == "__main__":
    main()
