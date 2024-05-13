"""MicrosoftEntraProviderGroup API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserGroupSerializer
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProviderGroup


class MicrosoftEntraProviderGroupSerializer(SourceSerializer):
    """MicrosoftEntraProviderGroup Serializer"""

    group_obj = UserGroupSerializer(source="group", read_only=True)

    class Meta:

        model = MicrosoftEntraProviderGroup
        fields = [
            "id",
            "group",
            "group_obj",
        ]


class MicrosoftEntraProviderGroupViewSet(UsedByMixin, ModelViewSet):
    """MicrosoftEntraProviderGroup Viewset"""

    queryset = MicrosoftEntraProviderGroup.objects.all().select_related("group")
    serializer_class = MicrosoftEntraProviderGroupSerializer
    filterset_fields = ["provider__id", "group__name", "group__group_uuid"]
    search_fields = ["provider__name", "group__name"]
    ordering = ["group__name"]
