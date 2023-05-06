"""interfaces API"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.interfaces.models import Interface


class InterfaceSerializer(ModelSerializer):
    """Interface serializer"""

    class Meta:
        model = Interface
        fields = [
            "interface_uuid",
            "url_name",
            "type",
            "template",
        ]


class InterfaceViewSet(UsedByMixin, ModelViewSet):
    """Interface serializer"""

    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    filterset_fields = ["url_name", "type", "template"]
    search_fields = ["url_name", "type", "template"]
