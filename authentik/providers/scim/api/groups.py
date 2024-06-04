"""SCIMProviderGroup API Views"""

from rest_framework import mixins
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserGroupSerializer
from authentik.providers.scim.models import SCIMProviderGroup


class SCIMProviderGroupSerializer(ModelSerializer):
    """SCIMProviderGroup Serializer"""

    group_obj = UserGroupSerializer(source="group", read_only=True)

    class Meta:

        model = SCIMProviderGroup
        fields = [
            "id",
            "scim_id",
            "group",
            "group_obj",
            "provider",
        ]


class SCIMProviderGroupViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """SCIMProviderGroup Viewset"""

    queryset = SCIMProviderGroup.objects.all().select_related("group")
    serializer_class = SCIMProviderGroupSerializer
    filterset_fields = ["provider__id", "group__name", "group__group_uuid"]
    search_fields = ["provider__name", "group__name"]
    ordering = ["group__name"]
