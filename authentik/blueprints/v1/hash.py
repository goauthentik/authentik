"""Blueprint hashing"""

from collections.abc import Generator
from hashlib import sha512
from pathlib import Path
from typing import Any

from yaml import load
from yaml.error import YAMLError

from authentik.blueprints.v1.common import BlueprintLoader, File, YAMLTag


def iter_file_tags(value: Any, ancestors: frozenset[int] = frozenset()) -> Generator[File]:
    """Find all `!File` tags in a loaded blueprint, including tags used as arguments
    of other tags. A node is not descended into again below itself; a node reached by
    several routes is visited once per route."""
    if id(value) in ancestors:
        return
    ancestors = ancestors | {id(value)}
    if isinstance(value, File):
        yield value
    if isinstance(value, dict):
        children = value.values()
    elif isinstance(value, list | tuple):
        children = value
    elif isinstance(value, YAMLTag):
        children = vars(value).values()
    else:
        return
    for child in children:
        yield from iter_file_tags(child, ancestors)


# One byte where a readable reference contributes a 64-byte digest
MISSING_FILE_MARKER = b"\0"


def blueprint_hash(content: str) -> str:
    """Hash a blueprint's content and the contents of the files it references with
    `!File` tags"""
    hasher = sha512(content.encode())
    try:
        raw_blueprint = load(content, BlueprintLoader)
    except YAMLError:
        return hasher.hexdigest()
    for tag in iter_file_tags(raw_blueprint):
        # Mapping-node tags have no path; nested tags cannot be resolved here
        path = getattr(tag, "path", None)
        if not isinstance(path, str):
            continue
        try:
            referenced = Path(path).read_bytes()
        except OSError, ValueError:
            # An unreadable reference still takes its place in the sequence, so a file
            # that goes missing while another appears cannot leave the hash unchanged
            hasher.update(MISSING_FILE_MARKER)
            continue
        hasher.update(sha512(referenced).digest())
    return hasher.hexdigest()
