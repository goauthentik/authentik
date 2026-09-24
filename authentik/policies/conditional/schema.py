"""Schema of the condition tree stored in conditional policies"""

from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from django.utils.translation import ngettext
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from pydantic import ValidationError as PydanticValidationError
from rest_framework.exceptions import ValidationError

from authentik.lib.pydantic import PydanticField
from authentik.policies.conditional.operators import ConditionOperatorName
from authentik.policies.conditional.types import ConditionCastKind

SCHEMA_VERSION = 1
MAX_DEPTH = 10
MAX_NODES = 200


class ConditionGroupOp(StrEnum):
    ALL = "all"
    ANY = "any"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConditionVariableRef(_Model):
    """Reference to a variable"""

    key: str
    param: str | None = Field(
        default=None, description="Path or key, for variables which take a parameter."
    )
    cast: ConditionCastKind | None = Field(
        default=None,
        description="Type to convert the value to, required for variables of type `any`.",
    )


class ConditionLiteralOperand(_Model):
    """Fixed value to compare against"""

    type: Literal["literal"]
    value: JsonValue


class ConditionVariableOperand(_Model):
    """Variable to compare against"""

    type: Literal["variable"]
    variable: ConditionVariableRef


ConditionOperand = Annotated[
    ConditionLiteralOperand | ConditionVariableOperand, Field(discriminator="type")
]


class ConditionOptions(_Model):
    case_sensitive: bool = True


class ConditionComparisonNode(_Model):
    """Compare a variable against a value"""

    type: Literal["condition"]
    variable: ConditionVariableRef
    operator: ConditionOperatorName
    value: ConditionOperand | None = None
    options: ConditionOptions = Field(default_factory=ConditionOptions)


class ConditionGroupNode(_Model):
    """Combine the results of multiple nodes"""

    type: Literal["group"]
    op: ConditionGroupOp
    children: list[ConditionNode]


class ConditionNotNode(_Model):
    """Negate the result of a node"""

    type: Literal["not"]
    child: ConditionNode


class ConditionPolicyNode(_Model):
    """Evaluate another policy"""

    type: Literal["policy"]
    policy: UUID


ConditionNode = Annotated[
    ConditionComparisonNode | ConditionGroupNode | ConditionNotNode | ConditionPolicyNode,
    Field(discriminator="type"),
]


class ConditionTree(_Model):
    """Condition tree of a conditional policy"""

    version: int = Field(ge=SCHEMA_VERSION, le=SCHEMA_VERSION)
    root: ConditionNode


# Values of the `type` field of nodes and operands, which pydantic includes in the location of
# validation errors within discriminated unions
_DISCRIMINATOR_TAGS = frozenset({"condition", "group", "not", "policy", "literal", "variable"})
# Fields which contain a discriminated union
_UNION_FIELDS = frozenset({"root", "child", "value"})


def error_path(loc: tuple[int | str, ...]) -> str:
    """Convert the location of a pydantic validation error into the dotted path of the node
    and field, for example `root.children.1.operator`"""
    parts: list[str] = []
    previous: int | str | None = None
    for part in loc:
        is_tag = isinstance(part, str) and part in _DISCRIMINATOR_TAGS
        if is_tag and (isinstance(previous, int) or previous in _UNION_FIELDS):
            previous = part
            continue
        parts.append(str(part))
        previous = part
    return ".".join(parts)


def condition_errors(errors: list[tuple[str, str]]) -> ValidationError:
    """Validation error for a condition tree, with messages grouped by the path of the node
    (and field) they belong to, so that they can be shown next to the node"""
    nodes: dict[str, list[str]] = {}
    for path, message in errors:
        nodes.setdefault(path or "root", []).append(message)
    detail = ngettext(
        "The conditions contain %(count)d error.",
        "The conditions contain %(count)d errors.",
        len(errors),
    ) % {"count": len(errors)}
    return ValidationError({"detail": detail, "nodes": nodes})


class ConditionTreeField(PydanticField):
    """Serializer field for a condition tree"""

    def __init__(self, **kwargs):
        super().__init__(
            ConditionTree,
            named_unions={"ConditionNode": ConditionNode, "ConditionOperand": ConditionOperand},
            **kwargs,
        )

    def to_internal_value(self, data: Any) -> dict:
        try:
            validated = ConditionTree.model_validate(data)
        except PydanticValidationError as exc:
            raise condition_errors(
                [(error_path(error["loc"]), error["msg"]) for error in exc.errors()]
            ) from exc
        return validated.model_dump(mode="json")


ConditionGroupNode.model_rebuild()
ConditionNotNode.model_rebuild()
ConditionTree.model_rebuild()
