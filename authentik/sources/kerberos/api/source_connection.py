from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
    UserSourceConnectionViewSet,
)
from authentik.sources.kerberos.models import (
    GroupKerberosSourceConnection,
    UserKerberosSourceConnection,
)


class UserKerberosSourceConnectionSerializer(UserSourceConnectionSerializer):
    class Meta(UserSourceConnectionSerializer.Meta):
        model = UserKerberosSourceConnection


class UserKerberosSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    queryset = UserKerberosSourceConnection.objects.all()
    serializer_class = UserKerberosSourceConnectionSerializer


class GroupKerberosSourceConnectionSerializer(GroupSourceConnectionSerializer):
    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupKerberosSourceConnection


class GroupKerberosSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    queryset = GroupKerberosSourceConnection.objects.all()
    serializer_class = GroupKerberosSourceConnectionSerializer
