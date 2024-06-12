"""MicrosoftEntraProviderUser API Views"""

from rest_framework import mixins
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.models import User
from authentik.enterprise.providers.microsoft_entra.clients.users import MicrosoftEntraUserClient
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProviderUser


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

    def perform_create(self, serializer: MicrosoftEntraProviderUserSerializer):
        super().perform_create(serializer)
        instance: MicrosoftEntraProviderUser = serializer.instance
        client: MicrosoftEntraUserClient = instance.provider.client_for_model(User)
        ms_user = client.fetch_single(instance.microsoft_id)
        instance.attributes = client.entity_as_dict(ms_user)
        instance.save()
