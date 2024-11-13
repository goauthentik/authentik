"""Application Roles API Viewset"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import GroupSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import (
    ApplicationEntitlement,
)


class ApplicationEntitlementSerializer(ModelSerializer):
    """ApplicationEntitlement Serializer"""

    group_obj = GroupSerializer(required=False, read_only=True, source="group")
    user_obj = UserSerializer(required=False, read_only=True, source="user")

    class Meta:
        model = ApplicationEntitlement
        fields = [
            "app_entitlement_uuid",
            "name",
            "app",
            "user",
            "group",
            "attributes",
            "group_obj",
            "user_obj",
        ]


class ApplicationEntitlementViewSet(UsedByMixin, ModelViewSet):
    """ApplicationEntitlement Viewset"""

    queryset = ApplicationEntitlement.objects.all()
    serializer_class = ApplicationEntitlementSerializer
    search_fields = [
        "app_entitlement_uuid",
        "name",
        "app",
        "user",
        "group",
        "attributes",
    ]
    filterset_fields = [
        "app_entitlement_uuid",
        "name",
        "app",
        "user",
        "group",
    ]
    ordering = ["name"]
