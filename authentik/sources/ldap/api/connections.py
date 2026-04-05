"""Source API Views"""


from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.ldap.models import (
    GroupLDAPSourceConnection,
    UserLDAPSourceConnection,
)


class UserLDAPSourceConnectionSerializer(UserSourceConnectionSerializer):
    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserLDAPSourceConnection


class UserLDAPSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    queryset = UserLDAPSourceConnection.objects.all()
    serializer_class = UserLDAPSourceConnectionSerializer


class GroupLDAPSourceConnectionSerializer(GroupSourceConnectionSerializer):
    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupLDAPSourceConnection


class GroupLDAPSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    queryset = GroupLDAPSourceConnection.objects.all()
    serializer_class = GroupLDAPSourceConnectionSerializer
