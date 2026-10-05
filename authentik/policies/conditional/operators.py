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

    @property
    def checks_presence(self) -> bool:
        """Presence checks are evaluated even if the value of the variable is missing"""
        return self.name in (ConditionOperatorName.IS_SET, ConditionOperatorName.IS_NOT_SET)

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
        return T.list(T.CIDR)

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

    @staticmethod
    def is_url(value: str, _) -> bool:
        try:
            DomainlessURLValidator(schemes=("http", "https"))(value)
        except ValidationError:
            return False
        return True


N = ConditionOperatorName
S = OperandShape
# Presence can be checked without knowing the type of a value
ALL = frozenset(TypeKind) - {TypeKind.DURATION, TypeKind.CIDR}
EQUAL = frozenset(
    {
        TypeKind.STRING,
        TypeKind.NUMBER,
        TypeKind.DATETIME,
        TypeKind.IP,
        TypeKind.ENUM,
        TypeKind.MODEL,
    }
)
ORDERED = frozenset({TypeKind.NUMBER, TypeKind.DATETIME})
STRING = frozenset({TypeKind.STRING})
LIST = frozenset({TypeKind.LIST})
BOOLEAN = frozenset({TypeKind.BOOLEAN})
DATETIME = frozenset({TypeKind.DATETIME})
IP = frozenset({TypeKind.IP})

OPERATORS: dict[str, Operator] = {
    op.name: op
    for op in [
        Operator(N.IS_SET, _("is set"), ALL, S.NONE, lambda a, b: True),
        Operator(N.IS_NOT_SET, _("is not set"), ALL, S.NONE, lambda a, b: False),
        Operator(N.EQ, _("equals"), EQUAL, S.SAME, lambda a, b: a == b),
        Operator(N.NE, _("does not equal"), EQUAL, S.SAME, lambda a, b: a != b),
        Operator(N.IN, _("is one of"), EQUAL, S.LIST_OF_SAME, lambda a, b: a in b),
        Operator(N.NOT_IN, _("is not one of"), EQUAL, S.LIST_OF_SAME, lambda a, b: a not in b),
        Operator(
            N.CONTAINS, _("contains"), STRING, S.SAME, lambda a, b: b in a, _("does not contain")
        ),
        Operator(
            N.STARTS_WITH,
            _("starts with"),
            STRING,
            S.SAME,
            lambda a, b: a.startswith(b),
            _("does not start with"),
        ),
        Operator(
            N.ENDS_WITH,
            _("ends with"),
            STRING,
            S.SAME,
            lambda a, b: a.endswith(b),
            _("does not end with"),
        ),
        # Case sensitivity of regular expressions is handled by the evaluator
        Operator(
            N.MATCHES,
            _("matches regular expression"),
            STRING,
            S.REGEX,
            lambda a, b: re.search(b, a) is not None,
            _("does not match regular expression"),
        ),
        Operator(N.LT, _("is less than"), ORDERED, S.SAME, lambda a, b: a < b),
        Operator(N.LTE, _("is less than or equal to"), ORDERED, S.SAME, lambda a, b: a <= b),
        Operator(N.GT, _("is greater than"), ORDERED, S.SAME, lambda a, b: a > b),
        Operator(N.GTE, _("is greater than or equal to"), ORDERED, S.SAME, lambda a, b: a >= b),
        Operator(
            N.BETWEEN,
            _("is between"),
            ORDERED,
            S.RANGE,
            lambda a, b: b[0] <= a <= b[1],
            _("is not between"),
        ),
        Operator(N.IS_TRUE, _("is true"), BOOLEAN, S.NONE, lambda a, b: a),
        Operator(N.IS_FALSE, _("is false"), BOOLEAN, S.NONE, lambda a, b: not a),
        Operator(
            N.WITHIN_LAST,
            _("is within the last"),
            DATETIME,
            S.DURATION,
            lambda a, b: a >= now() - b,
        ),
        Operator(
            N.OLDER_THAN, _("is older than"), DATETIME, S.DURATION, lambda a, b: a < now() - b
        ),
        Operator(
            N.IS_PRIVATE,
            _("is a private address"),
            IP,
            S.NONE,
            lambda a, b: a.is_private,
            _("is not a private address"),
        ),
        Operator(
            N.IS_GLOBAL,
            _("is a public address"),
            IP,
            S.NONE,
            lambda a, b: a.is_global,
            _("is not a public address"),
        ),
        Operator(
            N.IS_URL, _("is a valid URL"), STRING, S.NONE, Operator.is_url, _("is not a valid URL")
        ),
        Operator(
            N.IN_NETWORK,
            _("is in network"),
            IP,
            S.CIDR_LIST,
            lambda a, b: any(a in network for network in b),
            _("is not in network"),
        ),
        Operator(
            N.HAS_ITEM,
            _("contains item"),
            LIST,
            S.ITEM,
            lambda a, b: b in a,
            _("does not contain item"),
        ),
        Operator(
            N.HAS_ANY,
            _("contains any of"),
            LIST,
            S.LIST_OF_ITEM,
            lambda a, b: any(item in a for item in b),
            _("contains none of"),
        ),
        Operator(
            N.HAS_ALL,
            _("contains all of"),
            LIST,
            S.LIST_OF_ITEM,
            lambda a, b: all(item in a for item in b),
            _("does not contain all of"),
        ),
        Operator(N.IS_EMPTY, _("is empty"), LIST, S.NONE, lambda a, b: not a, _("is not empty")),
        Operator(N.LENGTH_EQ, _("has length"), LIST, S.NUMBER, lambda a, b: len(a) == b),
        Operator(
            N.LENGTH_GT, _("has length greater than"), LIST, S.NUMBER, lambda a, b: len(a) > b
        ),
        Operator(N.LENGTH_LT, _("has length less than"), LIST, S.NUMBER, lambda a, b: len(a) < b),
    ]
}
