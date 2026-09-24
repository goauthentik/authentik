"""Operators for conditional policies"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import TextChoices
from django.utils.functional import Promise
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from authentik.lib.models import DomainlessURLValidator
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


class ConditionOperatorName(StrEnum):
    """Names of all operators"""

    IS_SET = "is_set"
    IS_NOT_SET = "is_not_set"
    EQ = "eq"
    NE = "ne"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES = "matches"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    BETWEEN = "between"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    WITHIN_LAST = "within_last"
    OLDER_THAN = "older_than"
    IN_NETWORK = "in_network"
    IS_PRIVATE = "is_private"
    IS_GLOBAL = "is_global"
    IS_URL = "is_url"
    HAS_ITEM = "has_item"
    HAS_ANY = "has_any"
    HAS_ALL = "has_all"
    IS_EMPTY = "is_empty"
    LENGTH_EQ = "length_eq"
    LENGTH_GT = "length_gt"
    LENGTH_LT = "length_lt"


@dataclass(frozen=True)
class Operator:
    name: ConditionOperatorName
    label: str | Promise
    kinds: frozenset[TypeKind]
    operand: OperandShape
    func: Callable[[Any, Any], bool]
    # Label of the inverted operator, if the operator can be negated with the `negate` option.
    # Operators with an explicit opposite (like `eq` and `ne`) don't set this.
    negated_label: str | Promise | None = None

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
PRESENCE_OPERATORS = frozenset({ConditionOperatorName.IS_SET, ConditionOperatorName.IS_NOT_SET})

ALL_KINDS = frozenset(
    {
        # Presence can be checked without knowing the type of a value
        TypeKind.ANY,
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


def _is_url(value: str, _) -> bool:
    try:
        DomainlessURLValidator(schemes=("http", "https"))(value)
    except ValidationError:
        return False
    return True


OPERATORS: dict[str, Operator] = {
    op.name: op
    for op in [
        Operator(
            ConditionOperatorName.IS_SET,
            _("is set"),
            ALL_KINDS,
            OperandShape.NONE,
            lambda a, b: True,
        ),
        Operator(
            ConditionOperatorName.IS_NOT_SET,
            _("is not set"),
            ALL_KINDS,
            OperandShape.NONE,
            lambda a, b: False,
        ),
        Operator(
            ConditionOperatorName.EQ,
            _("equals"),
            EQUALITY_KINDS,
            OperandShape.SAME,
            lambda a, b: a == b,
        ),
        Operator(
            ConditionOperatorName.NE,
            _("does not equal"),
            EQUALITY_KINDS,
            OperandShape.SAME,
            lambda a, b: a != b,
        ),
        Operator(
            ConditionOperatorName.IN,
            _("is one of"),
            EQUALITY_KINDS,
            OperandShape.LIST_OF_SAME,
            lambda a, b: a in b,
        ),
        Operator(
            ConditionOperatorName.NOT_IN,
            _("is not one of"),
            EQUALITY_KINDS,
            OperandShape.LIST_OF_SAME,
            lambda a, b: a not in b,
        ),
        Operator(
            ConditionOperatorName.CONTAINS,
            _("contains"),
            STRING_KINDS,
            OperandShape.SAME,
            lambda a, b: b in a,
            negated_label=_("does not contain"),
        ),
        Operator(
            ConditionOperatorName.STARTS_WITH,
            _("starts with"),
            STRING_KINDS,
            OperandShape.SAME,
            lambda a, b: a.startswith(b),
            negated_label=_("does not start with"),
        ),
        Operator(
            ConditionOperatorName.ENDS_WITH,
            _("ends with"),
            STRING_KINDS,
            OperandShape.SAME,
            lambda a, b: a.endswith(b),
            negated_label=_("does not end with"),
        ),
        # Case sensitivity for regular expressions is handled by the evaluator
        Operator(
            ConditionOperatorName.MATCHES,
            _("matches regular expression"),
            STRING_KINDS,
            OperandShape.REGEX,
            lambda a, b: re.search(b, a) is not None,
            negated_label=_("does not match regular expression"),
        ),
        Operator(
            ConditionOperatorName.LT,
            _("is less than"),
            ORDERED_KINDS,
            OperandShape.SAME,
            lambda a, b: a < b,
        ),
        Operator(
            ConditionOperatorName.LTE,
            _("is less than or equal to"),
            ORDERED_KINDS,
            OperandShape.SAME,
            lambda a, b: a <= b,
        ),
        Operator(
            ConditionOperatorName.GT,
            _("is greater than"),
            ORDERED_KINDS,
            OperandShape.SAME,
            lambda a, b: a > b,
        ),
        Operator(
            ConditionOperatorName.GTE,
            _("is greater than or equal to"),
            ORDERED_KINDS,
            OperandShape.SAME,
            lambda a, b: a >= b,
        ),
        Operator(
            ConditionOperatorName.BETWEEN,
            _("is between"),
            ORDERED_KINDS,
            OperandShape.RANGE,
            lambda a, b: b[0] <= a <= b[1],
            negated_label=_("is not between"),
        ),
        Operator(
            ConditionOperatorName.IS_TRUE,
            _("is true"),
            frozenset({TypeKind.BOOLEAN}),
            OperandShape.NONE,
            lambda a, b: a,
        ),
        Operator(
            ConditionOperatorName.IS_FALSE,
            _("is false"),
            frozenset({TypeKind.BOOLEAN}),
            OperandShape.NONE,
            lambda a, b: not a,
        ),
        Operator(
            ConditionOperatorName.WITHIN_LAST,
            _("is within the last"),
            frozenset({TypeKind.DATETIME}),
            OperandShape.DURATION,
            _within_last,
        ),
        Operator(
            ConditionOperatorName.OLDER_THAN,
            _("is older than"),
            frozenset({TypeKind.DATETIME}),
            OperandShape.DURATION,
            _older_than,
        ),
        Operator(
            ConditionOperatorName.IS_PRIVATE,
            _("is a private address"),
            frozenset({TypeKind.IP}),
            OperandShape.NONE,
            lambda a, b: a.is_private,
            negated_label=_("is not a private address"),
        ),
        Operator(
            ConditionOperatorName.IS_GLOBAL,
            _("is a public address"),
            frozenset({TypeKind.IP}),
            OperandShape.NONE,
            lambda a, b: a.is_global,
            negated_label=_("is not a public address"),
        ),
        Operator(
            ConditionOperatorName.IS_URL,
            _("is a valid URL"),
            STRING_KINDS,
            OperandShape.NONE,
            _is_url,
            negated_label=_("is not a valid URL"),
        ),
        Operator(
            ConditionOperatorName.IN_NETWORK,
            _("is in network"),
            frozenset({TypeKind.IP}),
            OperandShape.CIDR_LIST,
            lambda a, b: any(a in network for network in b),
            negated_label=_("is not in network"),
        ),
        Operator(
            ConditionOperatorName.HAS_ITEM,
            _("contains item"),
            LIST_KINDS,
            OperandShape.ITEM,
            lambda a, b: b in a,
            negated_label=_("does not contain item"),
        ),
        Operator(
            ConditionOperatorName.HAS_ANY,
            _("contains any of"),
            LIST_KINDS,
            OperandShape.LIST_OF_ITEM,
            lambda a, b: any(item in a for item in b),
            negated_label=_("contains none of"),
        ),
        Operator(
            ConditionOperatorName.HAS_ALL,
            _("contains all of"),
            LIST_KINDS,
            OperandShape.LIST_OF_ITEM,
            lambda a, b: all(item in a for item in b),
            negated_label=_("does not contain all of"),
        ),
        Operator(
            ConditionOperatorName.IS_EMPTY,
            _("is empty"),
            LIST_KINDS,
            OperandShape.NONE,
            lambda a, b: len(a) == 0,
            negated_label=_("is not empty"),
        ),
        Operator(
            ConditionOperatorName.LENGTH_EQ,
            _("has length"),
            LIST_KINDS,
            OperandShape.NUMBER,
            lambda a, b: len(a) == b,
        ),
        Operator(
            ConditionOperatorName.LENGTH_GT,
            _("has length greater than"),
            LIST_KINDS,
            OperandShape.NUMBER,
            lambda a, b: len(a) > b,
        ),
        Operator(
            ConditionOperatorName.LENGTH_LT,
            _("has length less than"),
            LIST_KINDS,
            OperandShape.NUMBER,
            lambda a, b: len(a) < b,
        ),
    ]
}


def operators_for(vtype: ValueType) -> list[Operator]:
    """All operators applicable to a value of type `vtype`"""
    return [op for op in OPERATORS.values() if vtype.kind in op.kinds]
