"""SAML Session API Views"""

from rest_framework.fields import CharField

from authentik.core.api.utils import ModelSerializer
from authentik.providers.saml.models import SAMLSession


class SAMLSessionSerializer(ModelSerializer):
    """SAMLSession Serializer"""

    provider_name = CharField(source="provider.name", read_only=True)
    username = CharField(source="user.username", read_only=True)

    class Meta:
        model = SAMLSession
        fields = [
            "pk",
            "provider",
            "provider_name",
            "user",
            "username",
            "session",
            "session_index",
            "name_id",
            "name_id_format",
            "created",
            "expires",
            "expiring",
        ]
        read_only_fields = fields
