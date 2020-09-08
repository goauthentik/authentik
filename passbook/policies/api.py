"""policy API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.utils.model_meta import get_field_info
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from passbook.lib.api import InheritancePrimaryKeyRelatedField
from passbook.policies.forms import GENERAL_FIELDS
from passbook.policies.models import Policy, PolicyBinding, PolicyBindingModel


class PolicyBindingSerializer(ModelSerializer):
    """PolicyBinding Serializer"""

    # Because we're not interested in the PolicyBindingModel's PK but rather the subclasses PK,
    # we have to manually declare this field
    target = InheritancePrimaryKeyRelatedField(
        queryset=PolicyBindingModel.objects.all().select_subclasses(),
        source="target.pk",
        required=True,
    )

    def update(self, instance, validated_data):
        info = get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                if attr == "target":
                    instance.target_pk = value["pk"].pbm_uuid
                else:
                    setattr(instance, attr, value)

        instance.save()

        # Note that many-to-many fields are set after updating instance.
        # Setting m2m fields triggers signals which could potentially change
        # updated instance and we do not want it to collide with .update()
        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        return instance

    class Meta:

        model = PolicyBinding
        fields = ["pk", "policy", "target", "enabled", "order", "timeout"]


class PolicyBindingViewSet(ModelViewSet):
    """PolicyBinding Viewset"""

    queryset = PolicyBinding.objects.all()
    serializer_class = PolicyBindingSerializer


class PolicySerializer(ModelSerializer):
    """Policy Serializer"""

    __type__ = SerializerMethodField(method_name="get_type")

    def get_type(self, obj):
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("policy", "")

    class Meta:

        model = Policy
        fields = ["pk"] + GENERAL_FIELDS + ["__type__"]


class PolicyViewSet(ReadOnlyModelViewSet):
    """Policy Viewset"""

    queryset = Policy.objects.all()
    serializer_class = PolicySerializer

    def get_queryset(self):
        return Policy.objects.select_subclasses()
