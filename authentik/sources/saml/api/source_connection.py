"""SAML Source Serializer"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.saml.models import UserSAMLSourceConnection


class UserSAMLSourceConnectionSerializer(UserSourceConnectionSerializer):
    """SAML Source Serializer"""

    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserSAMLSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + ["identifier"]


class UserSAMLSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    """Source Viewset"""

    queryset = UserSAMLSourceConnection.objects.all()
    serializer_class = UserSAMLSourceConnectionSerializer
