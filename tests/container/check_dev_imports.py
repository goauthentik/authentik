"""Fail when shipped code imports a package that only the test kit provides.

The test kit appends its dev-only packages after the image's own, so such an import
passes the tests in the container, but fails in production.
Runs inside the server image with the test kit at /test-kit, see scripts/test_docker.sh.
"""

import ast
import re
import sys
from collections.abc import Iterator
from pathlib import Path

KIT = Path("/test-kit/devdeps")
# The shipped Python code, relative to /
SHIPPED = ["*.py", "authentik/**/*.py", "lifecycle/**/*.py", "ak-root/packages/**/*.py"]
TESTS = re.compile(r"/tests/|/tests\.py$")
# Development and test tools that ship with the code, but don't run in production
ALLOWED = {
    "/authentik/blueprints/v1/schema.py",
    "/authentik/core/management/commands/build_source_docs.py",
    "/authentik/core/management/commands/dev_server.py",
    "/authentik/lib/debug.py",
    "/authentik/root/test_plugin.py",
    "/authentik/root/test_runner.py",
    "/lifecycle/aws/app.py",
}


def top_level_names(path: Path) -> set[str]:
    """Names that are importable from a site-packages directory"""
    return {entry.name.split(".")[0] for entry in path.iterdir()}


def imported_names(path: Path) -> Iterator[tuple[int, str]]:
    """Absolute imports in a file, including the ones inside functions"""
    for node in ast.walk(ast.parse(path.read_bytes(), str(path))):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.lineno, node.module


def main() -> int:
    dev_only = top_level_names(KIT)
    found: dict[str, list[str]] = {}
    for pattern in SHIPPED:
        for path in sorted(Path("/").glob(pattern)):
            if TESTS.search(str(path)):
                continue
            for lineno, name in imported_names(path):
                if name.split(".")[0] in dev_only:
                    found.setdefault(str(path), []).append(f"line {lineno}: {name}")
    failed = False
    for file, imports in found.items():
        if file not in ALLOWED:
            print(f"{file} imports dev-only packages, {', '.join(imports)}")
            failed = True
    for file in sorted(ALLOWED - found.keys()):
        print(f"{file} no longer imports dev-only packages, remove it from ALLOWED")
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
