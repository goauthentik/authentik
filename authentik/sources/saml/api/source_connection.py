"""SAML Source Serializer"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.saml.models import GroupSAMLSourceConnection, UserSAMLSourceConnection


class UserSAMLSourceConnectionSerializer(UserSourceConnectionSerializer):
    """SAML Source Serializer"""

    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserSAMLSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + ["identifier"]


class UserSAMLSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    """Source Viewset"""

    queryset = UserSAMLSourceConnection.objects.all()
    serializer_class = UserSAMLSourceConnectionSerializer


class GroupSAMLSourceConnectionSerializer(GroupSourceConnectionSerializer):
    """OAuth Group-Source connection Serializer"""

    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupSAMLSourceConnection


class GroupSAMLSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    """Group-source connection Viewset"""

    queryset = GroupSAMLSourceConnection.objects.all()
    serializer_class = GroupSAMLSourceConnectionSerializer
