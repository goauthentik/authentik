"""Enterprise API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.models import License, validate_license


class LicenseSerializer(ModelSerializer):
    """License Serializer"""

    def validate_key(self, key: str) -> str:
        validate_license(key)
        return key

    class Meta:
        model = License
        fields = [
            "license_uuid",
            "name",
            "key",
            "expiry",
            "users",
            "external_users",
        ]
        extra_kwargs = {
            "name": {"read_only": True},
            "expiry": {"read_only": True},
            "users": {"read_only": True},
            "external_users": {"read_only": True},
        }


class LicenseViewSet(UsedByMixin, ModelViewSet):
    """License Viewset"""

    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    search_fields = ["name"]
    ordering = ["name"]
