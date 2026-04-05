from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.saml.models import GroupSAMLSourceConnection, UserSAMLSourceConnection


class UserSAMLSourceConnectionSerializer(UserSourceConnectionSerializer):
    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserSAMLSourceConnection


class UserSAMLSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    queryset = UserSAMLSourceConnection.objects.all()
    serializer_class = UserSAMLSourceConnectionSerializer


class GroupSAMLSourceConnectionSerializer(GroupSourceConnectionSerializer):
    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupSAMLSourceConnection


class GroupSAMLSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    queryset = GroupSAMLSourceConnection.objects.all()
    serializer_class = GroupSAMLSourceConnectionSerializer
