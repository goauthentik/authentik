"""Test utils"""

from inspect import currentframe
from pathlib import Path


def load_fixture(path: str, **kwargs) -> str:
    """Load fixture, optionally formatting it with kwargs"""
    current = currentframe()
    parent = current.f_back
    calling_file_path = parent.f_globals["__file__"]
    with open(Path(calling_file_path).resolve().parent / Path(path), encoding="utf-8") as _fixture:
        fixture = _fixture.read()
        try:
            return fixture % kwargs
        except (TypeError, ValueError):
            return fixture
