"""policy API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.policies.models import PolicyBinding


class PolicyBindingSerializer(ModelSerializer):
    """PolicyBinding Serializer"""

    class Meta:

        model = PolicyBinding
        fields = ["policy", "target", "enabled", "order"]


class PolicyBindingViewSet(ModelViewSet):
    """PolicyBinding Viewset"""

    queryset = PolicyBinding.objects.all()
    serializer_class = PolicyBindingSerializer
