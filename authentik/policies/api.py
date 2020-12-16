"""policy API Views"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField,
)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.policies.forms import GENERAL_FIELDS
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel


class PolicyBindingModelForeignKey(PrimaryKeyRelatedField):
    """rest_framework PrimaryKeyRelatedField which resolves
    model_manager's InheritanceQuerySet"""

    def use_pk_only_optimization(self):
        return False

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


class PolicySerializer(ModelSerializer):
    """Policy Serializer"""

    __type__ = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("policy", "")

    def to_representation(self, instance: Policy):
        # pyright: reportGeneralTypeIssues=false
        if instance.__class__ == Policy:
            return super().to_representation(instance)
        return instance.serializer(instance=instance).data

    class Meta:

        model = Policy
        fields = ["pk"] + GENERAL_FIELDS + ["__type__"]
        depth = 3


class PolicyViewSet(ReadOnlyModelViewSet):
    """Policy Viewset"""

    queryset = Policy.objects.all()
    serializer_class = PolicySerializer
    filterset_fields = {
        'bindings': ['isnull'],
        'promptstage': ['isnull'],
    }

    def get_queryset(self):
        return Policy.objects.select_subclasses()


class PolicyBindingSerializer(ModelSerializer):
    """PolicyBinding Serializer"""

    # Because we're not interested in the PolicyBindingModel's PK but rather the subclasses PK,
    # we have to manually declare this field
    target = PolicyBindingModelForeignKey(
        queryset=PolicyBindingModel.objects.select_subclasses(),
        required=True,
    )

    policy_obj = PolicySerializer(read_only=True, source="policy")

    class Meta:

        model = PolicyBinding
        fields = ["pk", "policy", "policy_obj", "target", "enabled", "order", "timeout"]


class PolicyBindingViewSet(ModelViewSet):
    """PolicyBinding Viewset"""

    queryset = PolicyBinding.objects.all()
    serializer_class = PolicyBindingSerializer
    filterset_fields = ["policy", "target", "enabled", "order", "timeout"]
    search_fields = ["policy__name"]
