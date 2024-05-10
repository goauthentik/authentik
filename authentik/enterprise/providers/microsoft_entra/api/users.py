"""MicrosoftEntraProviderUser API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProviderUser


class MicrosoftEntraProviderUserSerializer(SourceSerializer):
    """MicrosoftEntraProviderUser Serializer"""

    user_obj = GroupMemberSerializer(source="user", read_only=True)

    class Meta:

        model = MicrosoftEntraProviderUser
        fields = [
            "id",
            "user",
            "user_obj",
        ]


class MicrosoftEntraProviderUserViewSet(UsedByMixin, ModelViewSet):
    """MicrosoftEntraProviderUser Viewset"""

    queryset = MicrosoftEntraProviderUser.objects.all().select_related("user")
    serializer_class = MicrosoftEntraProviderUserSerializer
    filterset_fields = ["provider__id", "user__username", "user__id"]
    search_fields = ["provider__name", "user__username"]
    ordering = ["user__username"]
