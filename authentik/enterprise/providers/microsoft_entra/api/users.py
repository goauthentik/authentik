"""MicrosoftEntraProviderUser API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProviderUser
from authentik.lib.sync.outgoing.api import OutgoingSyncConnectionCreateMixin


class MicrosoftEntraProviderUserSerializer(ModelSerializer):
    """MicrosoftEntraProviderUser Serializer"""

    user_obj = GroupMemberSerializer(source="user", read_only=True)

    class Meta:

        model = MicrosoftEntraProviderUser
        fields = [
            "id",
            "microsoft_id",
            "user",
            "user_obj",
            "provider",
            "attributes",
        ]
        extra_kwargs = {"attributes": {"read_only": True}}


class MicrosoftEntraProviderUserViewSet(
    OutgoingSyncConnectionCreateMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """MicrosoftEntraProviderUser Viewset"""

    queryset = MicrosoftEntraProviderUser.objects.all().select_related("user")
    serializer_class = MicrosoftEntraProviderUserSerializer
    filterset_fields = ["provider__id", "user__username", "user__id"]
    search_fields = ["provider__name", "user__username"]
    ordering = ["user__username"]
