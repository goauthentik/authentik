"""Enterprise API Views"""
from dacite import from_dict
from jwt import PyJWTError, decode
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ValidationError
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.models import License, LicenseBody, get_licensing_key
from authentik.root.install_id import get_install_id


class LicenseSerializer(ModelSerializer):
    """License Serializer"""

    def validate_key(self, key: str) -> str:
        try:
            body = from_dict(LicenseBody, decode(
                key,
                get_licensing_key(),
                algorithms=["RS256"],
                options={
                    "verify_aud": False,
                },
            ))
        except PyJWTError:
            raise ValidationError("Unable to verify license")
        if body.install_id != get_install_id():
            raise ValidationError("Unable to verify license")
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
