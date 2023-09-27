"""policy binding API Views"""
from typing import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django_filters.filters import BooleanFilter, ModelMultipleChoiceFilter
from django_filters.filterset import FilterSet
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, ValidationError
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.groups import GroupSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserSerializer
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.models import PolicyBinding, PolicyBindingModel

LOGGER = get_logger()


class PolicyBindingModelForeignKey(PrimaryKeyRelatedField):
    """rest_framework PrimaryKeyRelatedField which resolves
    model_manager's InheritanceQuerySet"""

    def use_pk_only_optimization(self):
        return False

    # pylint: disable=inconsistent-return-statements
    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            # Due to inheritance, a direct DB lookup for the primary key
            # won't return anything. This is because the direct lookup
            # checks the PK of PolicyBindingModel (for example),
            # but we get given the Primary Key of the inheriting class
            for model in self.get_queryset().select_subclasses().all():
                if str(model.pk) == str(data):
                    return model
            # as a fallback we still try a direct lookup
            return self.get_queryset().get_subclass(pk=data)
        except ObjectDoesNotExist:
            self.fail("does_not_exist", pk_value=data)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data).__name__)

    def to_representation(self, value):
        correct_model = PolicyBindingModel.objects.get_subclass(pbm_uuid=value.pbm_uuid)
        return correct_model.pk


class PolicyBindingSerializer(ModelSerializer):
    """PolicyBinding Serializer"""

    # Because we're not interested in the PolicyBindingModel's PK but rather the subclasses PK,
    # we have to manually declare this field
    target = PolicyBindingModelForeignKey(
        queryset=PolicyBindingModel.objects.select_subclasses(),
        required=True,
    )

    policy_obj = PolicySerializer(required=False, read_only=True, source="policy")
    group_obj = GroupSerializer(required=False, read_only=True, source="group")
    user_obj = UserSerializer(required=False, read_only=True, source="user")

    class Meta:
        model = PolicyBinding
        fields = [
            "pk",
            "policy",
            "group",
            "user",
            "policy_obj",
            "group_obj",
            "user_obj",
            "target",
            "negate",
            "enabled",
            "order",
            "timeout",
            "failure_result",
        ]

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """Check that either policy, group or user is set."""
        count = sum(
            [
                bool(attrs.get("policy", None)),
                bool(attrs.get("group", None)),
                bool(attrs.get("user", None)),
            ]
        )
        invalid = count > 1
        empty = count < 1
        if invalid:
            raise ValidationError("Only one of 'policy', 'group' or 'user' can be set.")
        if empty:
            raise ValidationError("One of 'policy', 'group' or 'user' must be set.")
        return attrs


class PolicyBindingFilter(FilterSet):
    """Filter for PolicyBindings"""

    target_in = ModelMultipleChoiceFilter(
        field_name="target__pbm_uuid",
        to_field_name="pbm_uuid",
        queryset=PolicyBindingModel.objects.select_subclasses(),
    )
    policy__isnull = BooleanFilter("policy", "isnull")

    class Meta:
        model = PolicyBinding
        fields = ["policy", "policy__isnull", "target", "target_in", "enabled", "order", "timeout"]


class PolicyBindingViewSet(UsedByMixin, ModelViewSet):
    """PolicyBinding Viewset"""

    queryset = (
        PolicyBinding.objects.all()
        .select_related("target", "group", "user")
        .prefetch_related("policy")
    )  # prefetching policy so we resolve the subclass
    serializer_class = PolicyBindingSerializer
    search_fields = ["policy__name"]
    filterset_class = PolicyBindingFilter
    ordering = ["target", "order"]
