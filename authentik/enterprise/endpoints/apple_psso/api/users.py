"""AppleDeviceUser API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.endpoints.apple_psso.models import AppleDeviceUser


class AppleDeviceUserSerializer(ModelSerializer):
    """AppleDeviceUser Serializer"""

    class Meta:
        model = AppleDeviceUser
        fields = [
            "pk",
            "device",
            "user",
            "is_primary",
        ]


class AppleDeviceUserViewSet(UsedByMixin, ModelViewSet):
    """AppleDeviceUser Viewset"""

    queryset = AppleDeviceUser.objects.all()
    serializer_class = AppleDeviceUserSerializer
    filterset_fields = [
        "pk",
    ]
    search_fields = ["pk"]
    ordering = ["pk"]
