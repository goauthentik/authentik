"""MicrosoftEntraProviderGroup API Views"""

from rest_framework import mixins
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserGroupSerializer
from authentik.core.models import Group
from authentik.enterprise.providers.microsoft_entra.clients.groups import MicrosoftEntraGroupClient
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProviderGroup


class MicrosoftEntraProviderGroupSerializer(ModelSerializer):
    """MicrosoftEntraProviderGroup Serializer"""

    group_obj = UserGroupSerializer(source="group", read_only=True)

    class Meta:

        model = MicrosoftEntraProviderGroup
        fields = [
            "id",
            "microsoft_id",
            "group",
            "group_obj",
            "provider",
            "attributes",
        ]
        extra_kwargs = {"attributes": {"read_only": True}}


class MicrosoftEntraProviderGroupViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """MicrosoftEntraProviderGroup Viewset"""

    queryset = MicrosoftEntraProviderGroup.objects.all().select_related("group")
    serializer_class = MicrosoftEntraProviderGroupSerializer
    filterset_fields = ["provider__id", "group__name", "group__group_uuid"]
    search_fields = ["provider__name", "group__name"]
    ordering = ["group__name"]

    def perform_create(self, serializer: MicrosoftEntraProviderGroupSerializer):
        super().perform_create(serializer)
        instance: MicrosoftEntraProviderGroup = serializer.instance
        client: MicrosoftEntraGroupClient = instance.provider.client_for_model(Group)
        ms_group = client.fetch_single(instance.microsoft_id)
        instance.attributes = client.entity_as_dict(ms_group)
        instance.save()
