"""Application Roles API Viewset"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import (
    ApplicationEntitlement,
)


class ApplicationEntitlementSerializer(ModelSerializer):
    """ApplicationEntitlement Serializer"""

    class Meta:
        model = ApplicationEntitlement
        fields = [
            "pbm_uuid",
            "name",
            "app",
            "attributes",
        ]


class ApplicationEntitlementViewSet(UsedByMixin, ModelViewSet):
    """ApplicationEntitlement Viewset"""

    queryset = ApplicationEntitlement.objects.all()
    serializer_class = ApplicationEntitlementSerializer
    search_fields = [
        "pbm_uuid",
        "name",
        "app",
        "attributes",
    ]
    filterset_fields = [
        "pbm_uuid",
        "name",
        "app",
    ]
    ordering = ["name"]
