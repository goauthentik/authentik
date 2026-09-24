"""Type system for conditional policies"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network
from typing import Any

from django.db.models import Model, QuerySet, TextChoices
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware

from authentik.lib.utils.time import timedelta_from_string


class _Missing:
    """Sentinel for values which are not available in the current policy request"""

    def __repr__(self) -> str:
        return "MISSING"

    def __bool__(self) -> bool:
        return False


MISSING: Any = _Missing()


class TypeKind(TextChoices):
    """Kinds of values variables can have, and operands operators can take"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    IP = "ip"
    ENUM = "enum"
    MODEL = "model"
    LIST = "list"
    # Value of unknown type (for example JSON attributes), must be cast before comparing
    ANY = "any"
    # Only used as operands
    DURATION = "duration"
    CIDR = "cidr"


class ConditionCastKind(StrEnum):
    """Types a variable of kind `any` can be cast to"""

    STRING = TypeKind.STRING.value
    NUMBER = TypeKind.NUMBER.value
    BOOLEAN = TypeKind.BOOLEAN.value
    DATETIME = TypeKind.DATETIME.value
    IP = TypeKind.IP.value


@dataclass(frozen=True)
class ValueType:
    """Type of a variable or operand"""

    kind: TypeKind
    # Type of list items, only set for `list`
    item: ValueType | None = None
    # Choices as (value, label), only set for `enum`
    choices: tuple[tuple[str, str], ...] = field(default=(), compare=False)
    # Model label (`app_label.model_name`), only set for `model`
    model: str | None = None

    def __str__(self) -> str:
        if self.kind == TypeKind.LIST and self.item:
            return f"list[{self.item}]"
        if self.kind == TypeKind.MODEL:
            return f"model[{self.model}]"
        return str(self.kind)

    @property
    def is_textual(self) -> bool:
        """Whether this type contains strings which can be compared case-insensitively"""
        if self.kind == TypeKind.LIST and self.item:
            return self.item.is_textual
        return self.kind in (TypeKind.STRING, TypeKind.ENUM)


class T:
    """Shorthand constructors for value types"""

    STRING = ValueType(TypeKind.STRING)
    NUMBER = ValueType(TypeKind.NUMBER)
    BOOLEAN = ValueType(TypeKind.BOOLEAN)
    DATETIME = ValueType(TypeKind.DATETIME)
    IP = ValueType(TypeKind.IP)
    ANY = ValueType(TypeKind.ANY)
    DURATION = ValueType(TypeKind.DURATION)
    CIDR = ValueType(TypeKind.CIDR)

    @staticmethod
    def enum(choices: Iterable[tuple[str, Any]]) -> ValueType:
        return ValueType(
            TypeKind.ENUM, choices=tuple((str(value), str(label)) for value, label in choices)
        )

    @staticmethod
    def model(label: str) -> ValueType:
        return ValueType(TypeKind.MODEL, model=label.lower())

    @staticmethod
    def list(item: ValueType) -> ValueType:
        return ValueType(TypeKind.LIST, item=item)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = parse_datetime(value)
        if not parsed:
            raise ValueError(f"'{value}' is not a valid datetime")
    else:
        raise ValueError(f"'{value}' is not a valid datetime")
    if is_naive(parsed):
        parsed = make_aware(parsed)
    return parsed


def _coerce_number(value: Any) -> int | float:
    if isinstance(value, bool):
        raise ValueError(f"'{value}' is not a number")
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return float(value)
    raise ValueError(f"'{value}' is not a number")


def _coerce_boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return value.lower() == "true"
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    raise ValueError(f"'{value}' is not a boolean")


def coerce(value: Any, vtype: ValueType) -> Any:  # noqa: PLR0911, PLR0912
    """Convert `value` to the python representation of `vtype`, raising `ValueError`
    if not possible. Used for both literals and resolved variable values."""
    match vtype.kind:
        case TypeKind.STRING:
            if isinstance(value, dict | list | bool) or value is None:
                raise ValueError(f"'{value}' is not a string")
            return str(value)
        case TypeKind.ENUM:
            value = str(value)
            if vtype.choices and value not in (choice for choice, _ in vtype.choices):
                raise ValueError(f"'{value}' is not a valid choice")
            return value
        case TypeKind.NUMBER:
            return _coerce_number(value)
        case TypeKind.BOOLEAN:
            return _coerce_boolean(value)
        case TypeKind.DATETIME:
            return _coerce_datetime(value)
        case TypeKind.IP:
            if isinstance(value, IPv4Address | IPv6Address):
                return value
            return ip_address(str(value))
        case TypeKind.CIDR:
            if isinstance(value, IPv4Network | IPv6Network):
                return value
            return ip_network(str(value), strict=False)
        case TypeKind.DURATION:
            if isinstance(value, timedelta):
                return value
            try:
                return timedelta_from_string(str(value))
            except ValueError as exc:
                raise ValueError(
                    f"'{value}' is not a valid duration, use a format like 'hours=1;minutes=30'"
                ) from exc
        case TypeKind.MODEL:
            if isinstance(value, Model):
                return str(value.pk)
            if isinstance(value, dict | list | bool) or value is None:
                raise ValueError(f"'{value}' is not a valid object reference")
            return str(value)
        case TypeKind.LIST:
            if isinstance(value, QuerySet):
                value = list(value)
            if not isinstance(value, list | tuple | set | frozenset):
                raise ValueError(f"'{value}' is not a list")
            if not vtype.item:
                return list(value)
            return [coerce(item, vtype.item) for item in value]
        case TypeKind.ANY:
            return value
    raise ValueError(f"Unknown type {vtype}")


def dig(root: Any, path: str) -> Any:
    """Get the value at the dotted `path` in nested dictionaries, or `MISSING`"""
    value = root
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return MISSING
        value = value[part]
    return value
