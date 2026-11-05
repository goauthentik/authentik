"""Strict, bounded JSON parsing for untrusted documents"""

import re
from json import JSONDecodeError, loads
from typing import Any, NoReturn

from authentik.enterprise.providers.oauth2_cimd.constants import (
    JSON_MAX_ARRAY_ITEMS,
    JSON_MAX_DEPTH,
    JSON_MAX_OBJECT_MEMBERS,
)
from authentik.enterprise.providers.oauth2_cimd.errors import CIMDError

_MEDIA_TYPE_SUFFIX_RE = re.compile(r"^application/[a-z0-9!#$&^_.+-]+\+json$")


def media_type(content_type: str | None) -> str:
    """Media type of a Content-Type header, lowercased and without parameters"""
    return (content_type or "").split(";", 1)[0].strip().lower()


def is_json_media_type(content_type: str | None, *extra: str) -> bool:
    """True for application/json, application/*+json, or one of `extra`"""
    value = media_type(content_type)
    return value == "application/json" or value in extra or bool(_MEDIA_TYPE_SUFFIX_RE.match(value))


def _reject_constant(_value: str) -> NoReturn:
    raise ValueError("Non-finite numbers are not allowed")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    if len(pairs) > JSON_MAX_OBJECT_MEMBERS:
        raise ValueError("Too many object members")
    result = dict(pairs)
    if len(result) != len(pairs):
        # Duplicate members are parsed differently by different parsers
        raise ValueError("Duplicate object member")
    return result


def _nesting_exceeds(text: str, limit: int) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > limit:
                return True
        elif character in "]}":
            depth -= 1
    return False


def _check_arrays(value: Any) -> None:
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            if len(item) > JSON_MAX_ARRAY_ITEMS:
                raise ValueError("Array too long")
            stack.extend(item)
        elif isinstance(item, dict):
            stack.extend(item.values())


def parse_json_object(content: bytes, error: type[CIMDError]) -> dict[str, Any]:
    """Parse `content` as a UTF-8 JSON object with bounded depth, array and object sizes.

    Rejects duplicate members and non-finite numbers. Raises `error` with a fixed code."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise error("invalid_encoding", "Document is not valid UTF-8") from None
    # Depth is checked before parsing, so deep nesting can't exhaust the parser
    if _nesting_exceeds(text, JSON_MAX_DEPTH):
        raise error("json_too_deep", "Document is nested too deeply")
    try:
        value = loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        _check_arrays(value)
    except JSONDecodeError, ValueError, RecursionError:
        raise error("invalid_json", "Document is not acceptable JSON") from None
    if not isinstance(value, dict):
        raise error("invalid_json", "Document is not a JSON object")
    return value
