"""Blueprint hashing"""

from collections.abc import Generator
from hashlib import sha512
from os import getenv
from pathlib import Path
from typing import Any

from django.utils.crypto import salted_hmac
from yaml import load
from yaml.error import YAMLError

from authentik.blueprints.v1.common import BlueprintLoader, Env, File, YAMLTag


def iter_external_tags(
    value: Any, ancestors: frozenset[int] = frozenset()
) -> Generator[Env | File]:
    """Find all `!Env` and `!File` tags in a loaded blueprint, including tags used as
    arguments of other tags. A node is not descended into again below itself; a node
    reached by several routes is visited once per route."""
    if id(value) in ancestors:
        return
    ancestors = ancestors | {id(value)}
    if isinstance(value, Env | File):
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
        yield from iter_external_tags(child, ancestors)


# One byte where a readable value contributes a 64-byte digest
MISSING_VALUE_MARKER = b"\0"


def blueprint_hash(content: str) -> str:
    """Hash a blueprint's content and the current values of its `!Env` and `!File` tags.
    The values are keyed with the secret key, as the hash is visible in the API and a
    plain hash of a short secret could be brute-forced."""
    hasher = sha512(content.encode())
    try:
        raw_blueprint = load(content, BlueprintLoader)
    except YAMLError:
        return hasher.hexdigest()
    values = salted_hmac("goauthentik.io/blueprints/v1/external-values", b"", algorithm="sha512")
    has_values = False
    for tag in iter_external_tags(raw_blueprint):
        # Mapping-node tags have no key or path; nested tags cannot be resolved here
        if isinstance(tag, Env):
            key = getattr(tag, "key", None)
            if not isinstance(key, str):
                continue
            try:
                env = getenv(key)
            except ValueError:
                env = None
            value = None if env is None else env.encode(errors="surrogateescape")
        else:
            path = getattr(tag, "path", None)
            if not isinstance(path, str):
                continue
            try:
                value = Path(path).read_bytes()
            except OSError, ValueError:
                value = None
        has_values = True
        # A missing value still takes its place in the sequence, so a value that goes
        # missing while another appears cannot leave the hash unchanged
        values.update(MISSING_VALUE_MARKER if value is None else sha512(value).digest())
    if has_values:
        hasher.update(values.digest())
    return hasher.hexdigest()
