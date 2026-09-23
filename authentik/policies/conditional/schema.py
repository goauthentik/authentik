"""Schema of the condition tree stored in conditional policies"""

from typing import TYPE_CHECKING, Any

from django.utils.translation import gettext_lazy as _
from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import ResolvedComponent
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    Field,
    IntegerField,
    JSONField,
    ListField,
    UUIDField,
)

from authentik.core.api.utils import PassiveSerializer
from authentik.policies.conditional.operators import OPERATOR_CHOICES
from authentik.policies.conditional.types import CAST_KINDS

if TYPE_CHECKING:
    from authentik.blueprints.v1.schema import SchemaBuilder

SCHEMA_VERSION = 1
MAX_DEPTH = 10
MAX_NODES = 200


class NodeType:
    GROUP = "group"
    NOT = "not"
    CONDITION = "condition"
    POLICY = "policy"


class GroupOp:
    ALL = "all"
    ANY = "any"


GROUP_OPS = [GroupOp.ALL, GroupOp.ANY]


class OperandType:
    LITERAL = "literal"
    VARIABLE = "variable"


class ConditionVariableRefSerializer(PassiveSerializer):
    """Reference to a variable"""

    key = CharField()
    param = CharField(required=False, allow_null=True, allow_blank=True, default=None)
    cast = ChoiceField(
        choices=[str(kind) for kind in CAST_KINDS],
        required=False,
        allow_null=True,
        default=None,
        help_text=_("Type to convert the value to, required for variables of type `any`."),
    )


class ConditionLiteralOperandSerializer(PassiveSerializer):
    """Fixed value to compare against"""

    type = ChoiceField(choices=[(OperandType.LITERAL, OperandType.LITERAL)])
    value = JSONField()


class ConditionVariableOperandSerializer(PassiveSerializer):
    """Variable to compare against"""

    type = ChoiceField(choices=[(OperandType.VARIABLE, OperandType.VARIABLE)])
    variable = ConditionVariableRefSerializer()


class ConditionOptionsSerializer(PassiveSerializer):
    case_sensitive = BooleanField(default=True)


class _DiscriminatedField(Field):
    """Field which delegates to a serializer based on the value of the `type` key"""

    types: dict[str, type[PassiveSerializer]] = {}

    def to_internal_value(self, data: Any) -> dict:
        if not isinstance(data, dict):
            raise ValidationError(_("Expected an object."))
        serializer_class = self.types.get(data.get("type"))
        if not serializer_class:
            raise ValidationError(
                _("Invalid type, must be one of {types}.").format(types=", ".join(self.types))
            )
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def to_representation(self, value: dict) -> dict:
        serializer_class = self.types.get(value.get("type"))
        if not serializer_class:
            return value
        return serializer_class(value).data

    # Name of the definition in the blueprint schema
    blueprint_definition = ""

    def blueprint_schema(self, builder: SchemaBuilder) -> dict:
        return builder.define(
            self.blueprint_definition,
            lambda: {
                "oneOf": [builder.to_jsonschema(serializer()) for serializer in self.types.values()]
            },
        )


class OperandField(_DiscriminatedField):
    blueprint_definition = "conditional_policy_operand"
    types = {
        OperandType.LITERAL: ConditionLiteralOperandSerializer,
        OperandType.VARIABLE: ConditionVariableOperandSerializer,
    }


class NodeField(_DiscriminatedField):
    blueprint_definition = "conditional_policy_node"
    # Populated below, as node serializers reference this field
    types = {}


class ConditionComparisonNodeSerializer(PassiveSerializer):
    """Compare a variable against a value"""

    type = ChoiceField(choices=[(NodeType.CONDITION, NodeType.CONDITION)])
    variable = ConditionVariableRefSerializer()
    operator = ChoiceField(choices=OPERATOR_CHOICES)
    value = OperandField(required=False, allow_null=True, default=None)
    options = ConditionOptionsSerializer(required=False)


class ConditionGroupNodeSerializer(PassiveSerializer):
    """Combine the results of multiple nodes"""

    type = ChoiceField(choices=[(NodeType.GROUP, NodeType.GROUP)])
    op = ChoiceField(choices=GROUP_OPS)
    children = ListField(child=NodeField())


class ConditionNotNodeSerializer(PassiveSerializer):
    """Negate the result of a node"""

    type = ChoiceField(choices=[(NodeType.NOT, NodeType.NOT)])
    child = NodeField()


class ConditionPolicyNodeSerializer(PassiveSerializer):
    """Evaluate another policy"""

    type = ChoiceField(choices=[(NodeType.POLICY, NodeType.POLICY)])
    policy = UUIDField()

    def to_internal_value(self, data):
        validated = super().to_internal_value(data)
        # Store UUIDs as strings, as the tree is stored in a JSON field
        validated["policy"] = str(validated["policy"])
        return validated


NodeField.types = {
    NodeType.CONDITION: ConditionComparisonNodeSerializer,
    NodeType.GROUP: ConditionGroupNodeSerializer,
    NodeType.NOT: ConditionNotNodeSerializer,
    NodeType.POLICY: ConditionPolicyNodeSerializer,
}


class ConditionTreeSerializer(PassiveSerializer):
    """Condition tree of a conditional policy"""

    version = IntegerField(min_value=SCHEMA_VERSION, max_value=SCHEMA_VERSION)
    root = NodeField()


class ConditionTreeField(Field):
    """Field for the condition tree, which is stored as JSON"""

    def to_internal_value(self, data: Any) -> dict:
        serializer = ConditionTreeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return dict(serializer.validated_data)

    def to_representation(self, value: dict) -> dict:
        return value

    def blueprint_schema(self, builder: SchemaBuilder) -> dict:
        return builder.to_jsonschema(ConditionTreeSerializer())


def _discriminated_component(
    auto_schema, direction, name: str, types: dict[str, type[PassiveSerializer]]
) -> dict:
    """Register a `oneOf` component with a discriminator for the `type` field"""
    component_name = name
    if direction == "request":
        component_name += "Request"
    component = ResolvedComponent(
        name=component_name,
        type=ResolvedComponent.SCHEMA,
        object=f"{name}-{direction}",
    )
    if component in auto_schema.registry:
        return auto_schema.registry[component].ref
    # Register before resolving the members, as they may reference this component
    auto_schema.registry.register(component)
    members = {
        type_name: auto_schema.resolve_serializer(serializer, direction)
        for type_name, serializer in types.items()
    }
    component.schema = {
        "oneOf": [member.ref for member in members.values()],
        "discriminator": {
            "propertyName": "type",
            "mapping": {type_name: member.ref["$ref"] for type_name, member in members.items()},
        },
    }
    return component.ref


class NodeFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "authentik.policies.conditional.schema.NodeField"

    def map_serializer_field(self, auto_schema, direction):
        return _discriminated_component(auto_schema, direction, "ConditionNode", NodeField.types)


class OperandFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "authentik.policies.conditional.schema.OperandField"

    def map_serializer_field(self, auto_schema, direction):
        return _discriminated_component(
            auto_schema, direction, "ConditionOperand", OperandField.types
        )


class ConditionTreeFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "authentik.policies.conditional.schema.ConditionTreeField"

    def map_serializer_field(self, auto_schema, direction):
        return auto_schema.resolve_serializer(ConditionTreeSerializer, direction).ref
