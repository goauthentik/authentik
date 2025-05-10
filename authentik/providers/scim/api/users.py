"""SCIMProviderUser API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from authentik.common.sync.outgoing.api import OutgoingSyncConnectionCreateMixin
from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.providers.scim.models import SCIMProviderUser


class SCIMProviderUserSerializer(ModelSerializer):
    """SCIMProviderUser Serializer"""

    user_obj = GroupMemberSerializer(source="user", read_only=True)

    class Meta:

        model = SCIMProviderUser
        fields = [
            "id",
            "scim_id",
            "user",
            "user_obj",
            "provider",
            "attributes",
        ]
        extra_kwargs = {"attributes": {"read_only": True}}


class SCIMProviderUserViewSet(
    mixins.CreateModelMixin,
    OutgoingSyncConnectionCreateMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """SCIMProviderUser Viewset"""

    queryset = SCIMProviderUser.objects.all().select_related("user")
    serializer_class = SCIMProviderUserSerializer
    filterset_fields = ["provider__id", "user__username", "user__id"]
    search_fields = ["provider__name", "user__username"]
    ordering = ["user__username"]
