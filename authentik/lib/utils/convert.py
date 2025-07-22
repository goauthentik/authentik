"""Conversion utilities for data type normalization."""

from typing import Any


def ensure_string_id(id_value: Any) -> Any:
    """
    Convert integer IDs to strings for SCIM 2.0 compatibility.

    SCIM 2.0 specification allows both string and integer IDs, but authentik's
    pydantic validation expects string values. This utility ensures consistent
    string representation of IDs while preserving non-integer types unchanged.

    Args:
        id_value: The ID value to convert (could be int, str, None, etc.)

    Returns:
        String representation of the ID, or None if input is None/empty

    Examples:
        >>> ensure_string_id(123)
        '123'
        >>> ensure_string_id('456')
        '456'
        >>> ensure_string_id(None)
        None
        >>> ensure_string_id('')
        ''
    """
    if id_value is None:
        return None
    if isinstance(id_value, int):
        return str(id_value)
    return id_value
