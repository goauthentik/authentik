"""Schema of the actions stored in conditional policies"""

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

SCHEMA_VERSION = 2
MAX_DEPTH = 10
MAX_NODES = 200


class ConditionGroupOp(StrEnum):
    ALL = "all"
    ANY = "any"
    NONE = "none"


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
    negate: bool = Field(
        default=False,
        description="Invert the result of the comparison, for example 'does not contain'.",
    )


class ConditionComparisonNode(_Model):
    """Compare a variable against a value"""

    type: Literal["compare"]
    variable: ConditionVariableRef
    operator: ConditionOperatorName
    value: ConditionOperand | None = None
    options: ConditionOptions = Field(default_factory=ConditionOptions)


class ConditionGroupNode(_Model):
    """Combine the results of multiple conditions"""

    type: Literal["group"]
    op: ConditionGroupOp
    children: list[ConditionNode]


class ConditionPolicyNode(_Model):
    """Evaluate another policy"""

    type: Literal["policy"]
    policy: UUID


ConditionNode = Annotated[
    ConditionComparisonNode | ConditionGroupNode | ConditionPolicyNode,
    Field(discriminator="type"),
]


class PolicyActionTarget(_Model):
    """Reference to a value that can be set by an action"""

    key: str
    param: str | None = Field(default=None, description="Key, for targets which take a parameter.")


class _Action(_Model):
    enabled: bool = Field(default=True, description="Disabled actions are skipped.")


class PolicyActionCondition(_Action):
    """Check a condition, and stop with a failing result if it doesn't pass"""

    type: Literal["condition"]
    condition: ConditionNode


class PolicyActionIf(_Action):
    """Run actions depending on a condition"""

    type: Literal["if"]
    condition: ConditionNode
    then_actions: list[PolicyAction] = Field(
        default_factory=list, description="Actions run when the condition passes."
    )
    else_actions: list[PolicyAction] = Field(
        default_factory=list, description="Actions run when the condition doesn't pass."
    )


class PolicyActionSet(_Action):
    """Set a value, for example a key in the flow context"""

    type: Literal["set"]
    target: PolicyActionTarget
    value: ConditionOperand


class PolicyActionStopResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"


class PolicyActionStop(_Action):
    """Stop, and return a result"""

    type: Literal["stop"]
    result: PolicyActionStopResult
    message: str | None = Field(default=None, description="Message shown to the user.")


PolicyAction = Annotated[
    PolicyActionCondition | PolicyActionIf | PolicyActionSet | PolicyActionStop,
    Field(discriminator="type"),
]


class PolicyActions(_Model):
    """Actions of a conditional policy"""

    version: int = Field(ge=SCHEMA_VERSION, le=SCHEMA_VERSION)
    actions: list[PolicyAction]


# Values of the `type` field of actions, conditions and operands, which pydantic includes in the
# location of validation errors within discriminated unions
_DISCRIMINATOR_TAGS = frozenset(
    {
        "condition",
        "if",
        "set",
        "stop",
        "compare",
        "group",
        "policy",
        "literal",
        "variable",
    }
)
# Fields which contain a discriminated union (items of lists are handled separately)
_UNION_FIELDS = frozenset({"condition", "value"})


def error_path(loc: tuple[int | str, ...]) -> str:
    """Convert the location of a pydantic validation error into the dotted path of the action
    or condition and field, for example `actions.1.condition.children.0.operator`"""
    parts: list[str] = []
    expect_tag = False
    for part in loc:
        if expect_tag and isinstance(part, str) and part in _DISCRIMINATOR_TAGS:
            expect_tag = False
            continue
        parts.append(str(part))
        expect_tag = isinstance(part, int) or part in _UNION_FIELDS
    return ".".join(parts)


def condition_errors(errors: list[tuple[str, str]]) -> ValidationError:
    """Validation error for the actions of a policy, with messages grouped by the path of the
    action or condition (and field) they belong to, so that they can be shown next to it"""
    nodes: dict[str, list[str]] = {}
    for path, message in errors:
        nodes.setdefault(path or "actions", []).append(message)
    detail = ngettext(
        "The actions contain %(count)d error.",
        "The actions contain %(count)d errors.",
        len(errors),
    ) % {"count": len(errors)}
    return ValidationError({"detail": detail, "nodes": nodes})


class PolicyActionsField(PydanticField):
    """Serializer field for the actions of a policy"""

    def __init__(self, **kwargs):
        super().__init__(
            PolicyActions,
            named_unions={
                "PolicyAction": PolicyAction,
                "ConditionNode": ConditionNode,
                "ConditionOperand": ConditionOperand,
            },
            **kwargs,
        )

    def to_internal_value(self, data: Any) -> dict:
        try:
            validated = PolicyActions.model_validate(data)
        except PydanticValidationError as exc:
            raise condition_errors(
                [(error_path(error["loc"]), error["msg"]) for error in exc.errors()]
            ) from exc
        return validated.model_dump(mode="json")


ConditionGroupNode.model_rebuild()
PolicyActionIf.model_rebuild()
PolicyActions.model_rebuild()
