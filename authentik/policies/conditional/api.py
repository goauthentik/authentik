"""Conditional Policy API"""

from collections import defaultdict

from django.apps import apps
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework.decorators import action
from rest_framework.fields import (
    CharField,
    ChoiceField,
    DictField,
    ListField,
    SerializerMethodField,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.conditional.evaluator import (
    CompiledAction,
    CompiledCondition,
    CompiledPolicyRef,
    ConditionValidationError,
    Literal,
    compile_actions,
    iter_conditions,
)
from authentik.policies.conditional.models import ConditionalPolicy
from authentik.policies.conditional.operators import OPERATORS, OperandShape
from authentik.policies.conditional.registry import ParamKind, registry
from authentik.policies.conditional.schema import PolicyActionsField, condition_errors
from authentik.policies.conditional.types import TypeKind, ValueType
from authentik.policies.models import Policy


def _referenced_policies(actions: dict) -> set[str]:
    try:
        compiled = compile_actions(actions)
    except ConditionValidationError:
        return set()
    return {
        node.policy for node in iter_conditions(compiled) if isinstance(node, CompiledPolicyRef)
    }


def _label(obj: Model) -> str:
    for attr in ("name", "username"):
        value = getattr(obj, attr, None)
        if value:
            return str(value)
    return str(obj)


def object_labels(actions: tuple[CompiledAction, ...]) -> dict[str, str]:
    """Names of all objects referenced by actions, keyed by `<model>:<pk>`, so that they can
    be shown instead of their primary keys"""
    references: dict[str, set[str]] = defaultdict(set)
    for node in iter_conditions(actions):
        if isinstance(node, CompiledPolicyRef):
            references["authentik_policies.policy"].add(node.policy)
        if not isinstance(node, CompiledCondition) or not isinstance(node.operand, Literal):
            continue
        expected = node.operator.operand_type(node.variable.type)
        if not expected:
            continue
        model = expected.model or (expected.item.model if expected.item else None)
        if not model:
            continue
        values = node.operand.value
        references[model].update(
            str(value) for value in (values if isinstance(values, list) else [values])
        )
    labels = {}
    for model, pks in references.items():
        try:
            model_class = apps.get_model(model)
        except LookupError:
            continue
        queryset = model_class.objects.filter(pk__in=pks)
        if hasattr(queryset, "select_subclasses"):
            queryset = queryset.select_subclasses()
        try:
            for obj in queryset:
                labels[f"{model}:{obj.pk}"] = _label(obj)
        except DjangoValidationError, ValueError:
            continue
    return labels


class ConditionalPolicySerializer(PolicySerializer):
    """Conditional Policy Serializer"""

    labels = SerializerMethodField()

    @extend_schema_field(DictField(child=CharField()))
    def get_labels(self, instance: ConditionalPolicy) -> dict[str, str]:
        """Names of objects referenced by the actions, keyed by `<model>:<pk>`"""
        try:
            return object_labels(instance.compiled())
        except ConditionValidationError:
            return {}

    actions = PolicyActionsField()

    def validate_actions(self, actions: dict) -> dict:
        try:
            compiled = compile_actions(actions)
        except ConditionValidationError as exc:
            raise condition_errors(exc.errors) from exc
        references = [
            node for node in iter_conditions(compiled) if isinstance(node, CompiledPolicyRef)
        ]
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
        return actions

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
                pending |= _referenced_policies(policy.actions)
        return False

    class Meta:
        model = ConditionalPolicy
        fields = PolicySerializer.Meta.fields + [
            "labels",
            "actions",
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


class ConditionScenarioSerializer(PassiveSerializer):
    """Situation in which policies are evaluated, and the facts available in it"""

    key = CharField()
    label = CharField()
    description = CharField()
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


class ConditionSetterSerializer(PassiveSerializer):
    """Value which actions can set"""

    key = CharField()
    label = CharField()
    description = CharField()
    type = ConditionValueTypeSerializer()
    requires = ListField(
        child=CharField(), help_text=_("Available when any of these facts are available.")
    )
    param = ChoiceField(choices=ParamKind.choices)
    app = CharField(source="app_label")
    app_verbose_name = CharField()


class ConditionCatalogSerializer(PassiveSerializer):
    """Everything available to build conditional policies"""

    facts = ConditionFactSerializer(many=True)
    scenarios = ConditionScenarioSerializer(many=True)
    variables = ConditionVariableSerializer(many=True)
    setters = ConditionSetterSerializer(many=True)
    operators = ConditionOperatorSerializer(many=True)


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
        """Facts, scenarios, variables, setters and operators available to conditional policies"""
        data = {
            "facts": [
                {"key": fact.key, "label": str(fact.label), "description": str(fact.description)}
                for fact in sorted(registry.facts.values(), key=lambda f: f.key)
            ],
            "scenarios": [
                {
                    "key": scenario.key,
                    "label": str(scenario.label),
                    "description": str(scenario.description),
                    "facts": sorted(scenario.facts),
                }
                for scenario in registry.scenarios.values()
            ],
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
            "setters": [
                {
                    "key": setter.key,
                    "label": str(setter.label),
                    "description": str(setter.description),
                    "type": setter.type,
                    "requires": sorted(setter.requires),
                    "param": str(setter.param),
                    "app_label": setter.app_label,
                    "app_verbose_name": setter.app_verbose_name,
                }
                for setter in sorted(registry.setters.values(), key=lambda s: s.key)
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
