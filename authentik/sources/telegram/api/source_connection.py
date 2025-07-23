from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.telegram.models import GroupTelegramSourceConnection, UserTelegramSourceConnection


class UserTelegramSourceConnectionSerializer(UserSourceConnectionSerializer):
    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserTelegramSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields


class UserTelegramSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    queryset = UserTelegramSourceConnection.objects.all()
    serializer_class = UserTelegramSourceConnectionSerializer


class GroupTelegramSourceConnectionSerializer(GroupSourceConnectionSerializer):
    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupTelegramSourceConnection


class GroupTelegramSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    queryset = GroupTelegramSourceConnection.objects.all()
    serializer_class = GroupTelegramSourceConnectionSerializer
