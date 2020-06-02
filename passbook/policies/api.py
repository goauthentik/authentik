"""policy API Views"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from passbook.policies.forms import GENERAL_FIELDS
from passbook.policies.models import Policy, PolicyBinding


class PolicyBindingSerializer(ModelSerializer):
    """PolicyBinding Serializer"""

    class Meta:

        model = PolicyBinding
        fields = ["policy", "target", "enabled", "order", "timeout"]


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
