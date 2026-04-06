"""Source API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.core.api.users import PartialGroupSerializer
from authentik.sources.ldap.models import (
    GroupLDAPSourceConnection,
    UserLDAPSourceConnection,
)


class UserLDAPSourceConnectionSerializer(UserSourceConnectionSerializer):
    user_obj = PartialUserSerializer(source="user", read_only=True)

    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserLDAPSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + ["user_obj"]


class UserLDAPSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    queryset = UserLDAPSourceConnection.objects.all()
    serializer_class = UserLDAPSourceConnectionSerializer


class GroupLDAPSourceConnectionSerializer(GroupSourceConnectionSerializer):
    group_obj = PartialGroupSerializer(source="group", read_only=True)

    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupLDAPSourceConnection
        fields = GroupSourceConnectionSerializer.Meta.fields + ["group_obj"]


class GroupLDAPSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    queryset = GroupLDAPSourceConnection.objects.all()
    serializer_class = GroupLDAPSourceConnectionSerializer
