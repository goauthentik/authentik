"""Wrapper for lifecycle/ak, to be installed by poetry"""

from os import system
from pathlib import Path
from sys import argv


def main():
    """Wrapper around ak bash script"""
    current_path = Path(__file__)
    args = " ".join(argv[1:])
    system(f"{current_path.parent}/ak {args}")  # nosec


if __name__ == "__main__":
    main()
