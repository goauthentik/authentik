"""blueprint spec"""
from dataclasses import dataclass, field
from typing import Any, Optional

from authentik import __version__


@dataclass
class BlueprintMeta:
    """Meta information about a blueprint"""

    author: str = field(default="")
    version_constraints: dict = field(default_factory=dict)
    verified: bool = field(default=False)


@dataclass
class BlueprintSpec:
    """Root blueprint spec"""

    version: str = field(default="v2")
    meta: "BlueprintMeta" = field(default=BlueprintMeta())
    inputs: list["BlueprintInputs"] = field(default_factory=list)
    resources: list["BlueprintResource"] = field(default_factory=list)


@dataclass
class BlueprintInputs:
    """Single input, modeled after stages/prompt's Prompt"""

    # pylint: disable=invalid-name
    id: str
    label: str
    type: str  # FieldTypes.choices
    required: bool
    placeholder: str = field(default="")
    order: int = field(default=0)
    validators: list[str] = field(default_factory=list)


@dataclass
class BlueprintFilter:
    """Blueprint filter"""

    attribute: str
    value: Any
    type: str = field(default="query")
    children: Optional[list["BlueprintFilter"]] = field(default_factory=list)


@dataclass
class BlueprintResource:
    """an individual blueprint resource"""

    model_name: str
    # pylint: disable=invalid-name
    id: Optional[str] = field(default=None)
    filters: list["BlueprintFilter"] = field(default_factory=list)
    _with: dict = field(default_factory=dict)
