"""Conditional Policy API"""

from collections import defaultdict

from django.apps import apps
from django.core.exceptions import ValidationError as DjangoValidationError
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
from authentik.policies.conditional.evaluator import CompiledVariable, ConditionCompiler
from authentik.policies.conditional.models import ConditionalPolicy
from authentik.policies.conditional.operators import OPERATORS, OperandShape
from authentik.policies.conditional.registry import ParamKind, registry
from authentik.policies.conditional.schema import ConditionValidationError, PolicyActionsField
from authentik.policies.conditional.types import TypeKind, ValueType
from authentik.policies.models import Policy


class ConditionalPolicySerializer(PolicySerializer):
    """Conditional Policy Serializer"""

    labels = SerializerMethodField()
    actions = PolicyActionsField()

    @extend_schema_field(DictField(child=CharField()))
    def get_labels(self, instance: ConditionalPolicy) -> dict[str, str]:
        """Names of objects referenced by the actions, keyed by `<model>:<pk>`, so that they
        can be shown instead of their primary keys"""
        try:
            compiled = instance.compiled()
        except ConditionValidationError:
            return {}
        references = defaultdict(set)
        references["authentik_policies.policy"] = {ref.policy for ref in compiled.references}
        for node in compiled.conditions:
            expected = node.operator.operand_type(node.variable.type)
            model = expected and (expected.model or (expected.item and expected.item.model))
            if model and not isinstance(node.operand, CompiledVariable):
                values = node.operand if isinstance(node.operand, list) else [node.operand]
                references[model].update(str(value) for value in values)
        labels = {}
        for model, pks in references.items():
            queryset = apps.get_model(model).objects.filter(pk__in=pks)
            if hasattr(queryset, "select_subclasses"):
                queryset = queryset.select_subclasses()
            try:
                for obj in queryset:
                    labels[f"{model}:{obj.pk}"] = str(obj)
            except DjangoValidationError, ValueError:
                continue
        return labels

    def validate_actions(self, actions: dict) -> dict:
        try:
            references = ConditionCompiler.compile(actions).references
        except ConditionValidationError as exc:
            raise exc.as_api_error() from exc
        existing = Policy.objects.filter(pk__in=[ref.policy for ref in references])
        existing_pks = {str(pk) for pk in existing.values_list("pk", flat=True)}
        errors = []
        for ref in references:
            if ref.policy not in existing_pks:
                errors.append((ref.path, _("Referenced policy does not exist.")))
                continue
            # Check if the referenced policy (indirectly) references this policy
            seen, pending = set(), {ref.policy}
            while self.instance and pending:
                current = pending.pop()
                if current == str(self.instance.pk):
                    message = _("Referenced policy references this policy, creating a loop.")
                    errors.append((ref.path, message))
                    break
                seen.add(current)
                for policy in ConditionalPolicy.objects.filter(pk=current):
                    try:
                        pending |= {r.policy for r in policy.compiled().references} - seen
                    except ConditionValidationError:
                        continue
        if errors:
            raise ConditionValidationError(errors).as_api_error()
        return actions

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
        item = super().to_representation(instance.item) if instance.item else None
        return {**super().to_representation(instance), "item": item}


class ConditionKnownParamSerializer(PassiveSerializer):
    """Well-defined parameter of a variable, which can be picked directly"""

    key = CharField()
    label = CharField()
    type = ConditionValueTypeSerializer()


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
    app = CharField(source="app.label")
    app_verbose_name = CharField(source="app.verbose_name")


class ConditionVariableSerializer(ConditionSetterSerializer):
    """Variable available to conditional policies"""

    params = ConditionKnownParamSerializer(many=True)


class ConditionScenarioSerializer(PassiveSerializer):
    """Situation in which policies are evaluated, and the facts available in it"""

    key = CharField()
    label = CharField()
    description = CharField()
    facts = ListField(child=CharField())


@extend_schema_field({"$ref": "#/components/schemas/ConditionOperatorName"})
class OperatorNameField(CharField):
    """Name of an operator, typed with the enum used by the actions schema"""


class ConditionOperatorSerializer(PassiveSerializer):
    """Operator available to conditional policies"""

    name = OperatorNameField()
    label = CharField()
    kinds = ListField(child=ChoiceField(choices=TypeKind.choices))
    operand = ChoiceField(choices=OperandShape.choices)
    negated_label = CharField(
        allow_null=True, help_text=_("Label when negated, null if it can't be negated.")
    )


class ConditionCatalogSerializer(PassiveSerializer):
    """Everything available to build conditional policies"""

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
        """Scenarios, variables, setters and operators available to conditional policies"""
        catalog = {
            "scenarios": registry.scenarios.values(),
            "variables": sorted(registry.variables.values(), key=lambda v: v.key),
            "setters": sorted(registry.setters.values(), key=lambda s: s.key),
            "operators": OPERATORS.values(),
        }
        return Response(ConditionCatalogSerializer(catalog).data)
