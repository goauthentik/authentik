"""Kerberos Source Serializer"""

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
    """Kerberos Source Serializer"""

    class Meta:
        model = UserKerberosSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + ["identifier"]


class UserKerberosSourceConnectionViewSet(UserSourceConnectionViewSet, ModelViewSet):
    """Source Viewset"""

    queryset = UserKerberosSourceConnection.objects.all()
    serializer_class = UserKerberosSourceConnectionSerializer


class GroupKerberosSourceConnectionSerializer(GroupSourceConnectionSerializer):
    """OAuth Group-Source connection Serializer"""

    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupKerberosSourceConnection


class GroupKerberosSourceConnectionViewSet(GroupSourceConnectionViewSet, ModelViewSet):
    """Group-source connection Viewset"""

    queryset = GroupKerberosSourceConnection.objects.all()
    serializer_class = GroupKerberosSourceConnectionSerializer
