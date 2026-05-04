"""Wrapper for lifecycle/ak, to be installed by uv"""

import subprocess
from pathlib import Path
from sys import argv, exit


def main():
    """Wrapper around ak bash script"""
    script = Path(__file__).parent / "ak"
    res = subprocess.run([str(script), *argv[1:]], check=False)
    exit(res.returncode)


if __name__ == "__main__":
    main()
