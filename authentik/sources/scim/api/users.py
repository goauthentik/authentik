"""SCIMSourceUser API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.scim.models import SCIMSourceUser


class SCIMSourceUserSerializer(SourceSerializer):
    """SCIMSourceUser Serializer"""

    user_obj = GroupMemberSerializer(source="user", read_only=True)

    class Meta:

        model = SCIMSourceUser
        fields = [
            "id",
            "user",
            "user_obj",
            "source",
            "attributes",
        ]


class SCIMSourceUserViewSet(UsedByMixin, ModelViewSet):
    """SCIMSourceUser Viewset"""

    queryset = SCIMSourceUser.objects.all().select_related("user")
    serializer_class = SCIMSourceUserSerializer
    filterset_fields = ["source__slug", "user__username", "user__id"]
    search_fields = ["source__slug", "user__username", "attributes"]
    ordering = ["user__username"]
