"""blueprint spec"""
from dataclasses import dataclass, field

from authentik import __version__


@dataclass
class BlueprintMeta:
    """Meta information about a blueprint"""

    author: str = field(default="")
    version: str = field(default="")
    required_authentik_version: str = field(default=__version__)
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

    field_key: str
    label: str
    type: str  # FieldTypes.choices
    required: bool
    placeholder: str = field(default="")
    order: int = field(default=0)


@dataclass
class BlueprintResource:
    """an individual blueprint resource"""

    model: str
    identifiers: dict
    attrs: dict
