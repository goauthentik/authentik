"""AppleDeviceConnection API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.endpoints.apple_psso.models import AppleDeviceConnection


class AppleDeviceConnectionSerializer(ModelSerializer):
    """AppleDeviceConnection Serializer"""

    class Meta:
        model = AppleDeviceConnection
        fields = [
            "pk",
            "sign_key_id",
            "enc_key_id",
        ]


class AppleDeviceConnectionViewSet(UsedByMixin, ModelViewSet):
    """AppleDeviceConnection Viewset"""

    queryset = AppleDeviceConnection.objects.all()
    serializer_class = AppleDeviceConnectionSerializer
    filterset_fields = [
        "pk",
    ]
    search_fields = ["pk"]
    ordering = ["pk"]
