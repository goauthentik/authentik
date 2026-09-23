"""Schema of the condition tree stored in conditional policies"""

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue

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


def ConditionTreeField(**kwargs) -> PydanticField:  # noqa: N802
    """Serializer field for a condition tree"""
    return PydanticField(
        ConditionTree,
        named_unions={"ConditionNode": ConditionNode, "ConditionOperand": ConditionOperand},
        **kwargs,
    )


ConditionGroupNode.model_rebuild()
ConditionNotNode.model_rebuild()
ConditionTree.model_rebuild()
