"""policy binding API Views"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.groups import GroupSerializer
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
            for model in self.get_queryset().select_subclasses().all().select_related():
                if model.pk == data:
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

    group = GroupSerializer(required=False)

    class Meta:

        model = PolicyBinding
        fields = [
            "pk",
            "policy",
            "group",
            "user",
            "target",
            "enabled",
            "order",
            "timeout",
        ]
        depth = 2


class PolicyBindingViewSet(ModelViewSet):
    """PolicyBinding Viewset"""

    queryset = PolicyBinding.objects.all().select_related(
        "policy", "target", "group", "user"
    )
    serializer_class = PolicyBindingSerializer
    filterset_fields = ["policy", "target", "enabled", "order", "timeout"]
    search_fields = ["policy__name"]
