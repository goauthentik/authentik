"""Conditional Policy API"""

from django.apps import apps
from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, ChoiceField, ListField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.conditional.evaluator import (
    CompiledPolicyRef,
    ConditionValidationError,
    compile_conditions,
    iter_nodes,
)
from authentik.policies.conditional.models import ConditionalPolicy
from authentik.policies.conditional.operators import OPERATORS, OperandShape
from authentik.policies.conditional.registry import ParamKind, registry
from authentik.policies.conditional.schema import ConditionTreeField, condition_errors
from authentik.policies.conditional.types import TypeKind, ValueType
from authentik.policies.models import Policy, PolicyBindingModel


def _referenced_policies(tree: dict) -> set[str]:
    try:
        root = compile_conditions(tree)
    except ConditionValidationError:
        return set()
    return {node.policy for node in iter_nodes(root) if isinstance(node, CompiledPolicyRef)}


class ConditionalPolicySerializer(PolicySerializer):
    """Conditional Policy Serializer"""

    conditions = ConditionTreeField()

    def validate_conditions(self, conditions: dict) -> dict:
        try:
            root = compile_conditions(conditions)
        except ConditionValidationError as exc:
            raise condition_errors(exc.errors) from exc
        references = [node for node in iter_nodes(root) if isinstance(node, CompiledPolicyRef)]
        existing = {
            str(pk)
            for pk in Policy.objects.filter(
                pk__in=[node.policy for node in references]
            ).values_list("pk", flat=True)
        }
        errors = []
        for node in references:
            if node.policy not in existing:
                errors.append((node.path, _("Referenced policy does not exist.")))
            elif self._creates_loop(node.policy):
                errors.append(
                    (
                        node.path,
                        _("Referenced policy references this policy, which would create a loop."),
                    )
                )
        if errors:
            raise condition_errors(errors)
        return conditions

    def _creates_loop(self, referenced: str) -> bool:
        """Check if the referenced policy (indirectly) references this policy"""
        if not self.instance:
            return False
        own_pk = str(self.instance.pk)
        seen: set[str] = set()
        pending = {referenced}
        while pending:
            current = pending.pop()
            if current == own_pk:
                return True
            if current in seen:
                continue
            seen.add(current)
            policy = ConditionalPolicy.objects.filter(pk=current).first()
            if policy:
                pending |= _referenced_policies(policy.conditions)
        return False

    class Meta:
        model = ConditionalPolicy
        fields = PolicySerializer.Meta.fields + [
            "conditions",
            "missing_behavior",
            "failure_message",
        ]


class ConditionChoiceSerializer(PassiveSerializer):
    value = CharField()
    label = CharField()


class ConditionItemTypeSerializer(PassiveSerializer):
    """Type of a list item"""

    kind = ChoiceField(choices=TypeKind.choices)
    model = CharField(required=False, allow_null=True)
    choices = ConditionChoiceSerializer(many=True)

    def to_representation(self, instance: ValueType) -> dict:
        return {
            "kind": str(instance.kind),
            "model": instance.model,
            "choices": [{"value": value, "label": label} for value, label in instance.choices],
        }


class ConditionValueTypeSerializer(ConditionItemTypeSerializer):
    """Type of a variable"""

    item = ConditionItemTypeSerializer(required=False, allow_null=True)

    def to_representation(self, instance: ValueType) -> dict:
        data = super().to_representation(instance)
        data["item"] = ConditionItemTypeSerializer(instance.item).data if instance.item else None
        return data


class ConditionKnownParamSerializer(PassiveSerializer):
    """Well-defined parameter of a variable, which can be picked directly"""

    key = CharField()
    label = CharField()
    type = ConditionValueTypeSerializer()


class ConditionVariableSerializer(PassiveSerializer):
    """Variable available to conditional policies"""

    key = CharField()
    label = CharField()
    description = CharField()
    type = ConditionValueTypeSerializer()
    requires = ListField(
        child=CharField(), help_text=_("Available when any of these facts are available.")
    )
    param = ChoiceField(choices=ParamKind.choices)
    params = ConditionKnownParamSerializer(many=True)
    app = CharField(source="app_label")
    app_verbose_name = CharField()


class ConditionFactSerializer(PassiveSerializer):
    """Data a policy request can carry"""

    key = CharField()
    label = CharField()
    description = CharField()


class ConditionTargetSerializer(PassiveSerializer):
    """Object policies can be bound to, and the facts available when they are evaluated"""

    model = CharField()
    verbose_name = CharField()
    facts = ListField(child=CharField())


class ConditionOperatorSerializer(PassiveSerializer):
    """Operator available to conditional policies"""

    name = CharField()
    label = CharField()
    kinds = ListField(child=ChoiceField(choices=TypeKind.choices))
    operand = ChoiceField(choices=OperandShape.choices)
    negated_label = CharField(
        allow_null=True, help_text=_("Label when negated, null if it can't be negated.")
    )


class ConditionCatalogSerializer(PassiveSerializer):
    """Everything available to build conditional policies"""

    facts = ConditionFactSerializer(many=True)
    targets = ConditionTargetSerializer(many=True)
    variables = ConditionVariableSerializer(many=True)
    operators = ConditionOperatorSerializer(many=True)


def _targets() -> list[dict]:
    """All models policies can be bound to, and their facts"""
    models: dict[str, type[Model]] = {}
    for model in apps.get_models():
        if issubclass(model, PolicyBindingModel) and model is not PolicyBindingModel:
            models[model._meta.label_lower] = model
    for label in registry.targets:
        if label not in models:
            try:
                models[label] = apps.get_model(label)
            except LookupError:
                continue
    return [
        {
            "model": label,
            "verbose_name": str(model._meta.verbose_name),
            "facts": sorted(registry.facts_for_target(label)),
        }
        for label, model in sorted(models.items())
    ]


class ConditionalPolicyViewSet(UsedByMixin, ModelViewSet):
    """Conditional Policy Viewset"""

    queryset = ConditionalPolicy.objects.all()
    serializer_class = ConditionalPolicySerializer
    filterset_fields = ["name", "missing_behavior", "execution_logging"]
    ordering = ["name"]
    search_fields = ["name"]

    @extend_schema(responses={200: ConditionCatalogSerializer})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def catalog(self, request: Request) -> Response:
        """Facts, targets, variables and operators available to conditional policies"""
        data = {
            "facts": [
                {"key": fact.key, "label": str(fact.label), "description": str(fact.description)}
                for fact in sorted(registry.facts.values(), key=lambda f: f.key)
            ],
            "targets": _targets(),
            "variables": [
                {
                    "key": variable.key,
                    "label": str(variable.label),
                    "description": str(variable.description),
                    "type": variable.type,
                    "requires": sorted(variable.requires),
                    "param": str(variable.param),
                    "params": [
                        {"key": param.key, "label": str(param.label), "type": param.type}
                        for param in variable.params
                    ],
                    "app_label": variable.app_label,
                    "app_verbose_name": variable.app_verbose_name,
                }
                for variable in sorted(registry.variables.values(), key=lambda v: v.key)
            ],
            "operators": [
                {
                    "name": op.name,
                    "label": str(op.label),
                    "kinds": sorted(str(kind) for kind in op.kinds),
                    "operand": str(op.operand),
                    "negated_label": str(op.negated_label) if op.negated_label else None,
                }
                for op in OPERATORS.values()
            ],
        }
        return Response(ConditionCatalogSerializer(data).data)
