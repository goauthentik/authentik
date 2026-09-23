"""Operators for conditional policies"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django.db.models import TextChoices
from django.utils.functional import Promise
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from authentik.policies.conditional.types import T, TypeKind, ValueType

MAX_REGEX_LENGTH = 256


class OperandShape(TextChoices):
    """Shape of the operand an operator expects, relative to the type of the variable"""

    NONE = "none"
    # Same type as the variable
    SAME = "same"
    # List of values of the same type as the variable
    LIST_OF_SAME = "list_of_same"
    # Two values of the same type as the variable
    RANGE = "range"
    # Same type as the items of the (list) variable
    ITEM = "item"
    # List of values of the same type as the items of the (list) variable
    LIST_OF_ITEM = "list_of_item"
    NUMBER = "number"
    DURATION = "duration"
    REGEX = "regex"
    CIDR_LIST = "cidr_list"


@dataclass(frozen=True)
class Operator:
    name: str
    label: str | Promise
    kinds: frozenset[TypeKind]
    operand: OperandShape
    func: Callable[[Any, Any], bool]

    def operand_type(self, vtype: ValueType) -> ValueType | None:
        """Type of the operand this operator expects for a variable of type `vtype`"""
        match self.operand:
            case OperandShape.NONE:
                return None
            case OperandShape.SAME:
                return vtype
            case OperandShape.LIST_OF_SAME | OperandShape.RANGE:
                return T.list(vtype)
            case OperandShape.ITEM:
                return vtype.item or T.ANY
            case OperandShape.LIST_OF_ITEM:
                return T.list(vtype.item or T.ANY)
            case OperandShape.NUMBER:
                return T.NUMBER
            case OperandShape.DURATION:
                return T.DURATION
            case OperandShape.REGEX:
                return T.STRING
            case OperandShape.CIDR_LIST:
                return T.list(T.CIDR)
        raise ValueError(f"Unknown operand shape {self.operand}")

    def validate_operand(self, operand: Any):
        """Additional validation of a literal operand, after it has been coerced"""
        if self.operand == OperandShape.RANGE and len(operand) != 2:  # noqa: PLR2004
            raise ValueError("Operand must be a list of exactly two values")
        if self.operand == OperandShape.REGEX:
            if len(operand) > MAX_REGEX_LENGTH:
                raise ValueError(f"Regular expression must be at most {MAX_REGEX_LENGTH} long")
            try:
                re.compile(operand)
            except re.error as exc:
                raise ValueError(f"Invalid regular expression: {exc}") from exc


# Operators which check for the presence of a value, and are evaluated even if the value
# of the variable is missing
PRESENCE_OPERATORS = frozenset({"is_set", "is_not_set"})

ALL_KINDS = frozenset(
    {
        TypeKind.STRING,
        TypeKind.NUMBER,
        TypeKind.BOOLEAN,
        TypeKind.DATETIME,
        TypeKind.IP,
        TypeKind.ENUM,
        TypeKind.MODEL,
        TypeKind.LIST,
    }
)
EQUALITY_KINDS = frozenset(
    {
        TypeKind.STRING,
        TypeKind.NUMBER,
        TypeKind.DATETIME,
        TypeKind.IP,
        TypeKind.ENUM,
        TypeKind.MODEL,
    }
)
ORDERED_KINDS = frozenset({TypeKind.NUMBER, TypeKind.DATETIME})
STRING_KINDS = frozenset({TypeKind.STRING})
LIST_KINDS = frozenset({TypeKind.LIST})


def _within_last(value, duration) -> bool:
    return value >= now() - duration


def _older_than(value, duration) -> bool:
    return value < now() - duration


OPERATORS: dict[str, Operator] = {
    op.name: op
    for op in [
        Operator("is_set", _("is set"), ALL_KINDS, OperandShape.NONE, lambda a, b: True),
        Operator("is_not_set", _("is not set"), ALL_KINDS, OperandShape.NONE, lambda a, b: False),
        Operator("eq", _("equals"), EQUALITY_KINDS, OperandShape.SAME, lambda a, b: a == b),
        Operator("ne", _("does not equal"), EQUALITY_KINDS, OperandShape.SAME, lambda a, b: a != b),
        Operator(
            "in", _("is one of"), EQUALITY_KINDS, OperandShape.LIST_OF_SAME, lambda a, b: a in b
        ),
        Operator(
            "not_in",
            _("is not one of"),
            EQUALITY_KINDS,
            OperandShape.LIST_OF_SAME,
            lambda a, b: a not in b,
        ),
        Operator("contains", _("contains"), STRING_KINDS, OperandShape.SAME, lambda a, b: b in a),
        Operator(
            "starts_with",
            _("starts with"),
            STRING_KINDS,
            OperandShape.SAME,
            lambda a, b: a.startswith(b),
        ),
        Operator(
            "ends_with", _("ends with"), STRING_KINDS, OperandShape.SAME, lambda a, b: a.endswith(b)
        ),
        # Case sensitivity for regular expressions is handled by the evaluator
        Operator(
            "matches",
            _("matches regular expression"),
            STRING_KINDS,
            OperandShape.REGEX,
            lambda a, b: re.search(b, a) is not None,
        ),
        Operator("lt", _("is less than"), ORDERED_KINDS, OperandShape.SAME, lambda a, b: a < b),
        Operator(
            "lte",
            _("is less than or equal to"),
            ORDERED_KINDS,
            OperandShape.SAME,
            lambda a, b: a <= b,
        ),
        Operator("gt", _("is greater than"), ORDERED_KINDS, OperandShape.SAME, lambda a, b: a > b),
        Operator(
            "gte",
            _("is greater than or equal to"),
            ORDERED_KINDS,
            OperandShape.SAME,
            lambda a, b: a >= b,
        ),
        Operator(
            "between",
            _("is between"),
            ORDERED_KINDS,
            OperandShape.RANGE,
            lambda a, b: b[0] <= a <= b[1],
        ),
        Operator(
            "is_true",
            _("is true"),
            frozenset({TypeKind.BOOLEAN}),
            OperandShape.NONE,
            lambda a, b: a,
        ),
        Operator(
            "is_false",
            _("is false"),
            frozenset({TypeKind.BOOLEAN}),
            OperandShape.NONE,
            lambda a, b: not a,
        ),
        Operator(
            "within_last",
            _("is within the last"),
            frozenset({TypeKind.DATETIME}),
            OperandShape.DURATION,
            _within_last,
        ),
        Operator(
            "older_than",
            _("is older than"),
            frozenset({TypeKind.DATETIME}),
            OperandShape.DURATION,
            _older_than,
        ),
        Operator(
            "in_network",
            _("is in network"),
            frozenset({TypeKind.IP}),
            OperandShape.CIDR_LIST,
            lambda a, b: any(a in network for network in b),
        ),
        Operator(
            "has_item", _("contains item"), LIST_KINDS, OperandShape.ITEM, lambda a, b: b in a
        ),
        Operator(
            "has_any",
            _("contains any of"),
            LIST_KINDS,
            OperandShape.LIST_OF_ITEM,
            lambda a, b: any(item in a for item in b),
        ),
        Operator(
            "has_all",
            _("contains all of"),
            LIST_KINDS,
            OperandShape.LIST_OF_ITEM,
            lambda a, b: all(item in a for item in b),
        ),
        Operator(
            "is_empty", _("is empty"), LIST_KINDS, OperandShape.NONE, lambda a, b: len(a) == 0
        ),
        Operator(
            "length_eq",
            _("has length"),
            LIST_KINDS,
            OperandShape.NUMBER,
            lambda a, b: len(a) == b,
        ),
        Operator(
            "length_gt",
            _("has length greater than"),
            LIST_KINDS,
            OperandShape.NUMBER,
            lambda a, b: len(a) > b,
        ),
        Operator(
            "length_lt",
            _("has length less than"),
            LIST_KINDS,
            OperandShape.NUMBER,
            lambda a, b: len(a) < b,
        ),
    ]
}


OPERATOR_CHOICES = [(op.name, op.label) for op in OPERATORS.values()]


def operators_for(vtype: ValueType) -> list[Operator]:
    """All operators applicable to a value of type `vtype`"""
    return [op for op in OPERATORS.values() if vtype.kind in op.kinds]
