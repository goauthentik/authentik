"""Application Roles API Viewset"""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import (
    Application,
    ApplicationEntitlement,
    User,
)


class ApplicationEntitlementSerializer(ModelSerializer):
    """ApplicationEntitlement Serializer"""

    def validate_app(self, app: Application) -> Application:
        """Ensure user has permission to view"""
        user: User = self._context["request"].user
        if user.has_perm("view_application", app) or user.has_perm(
            "authentik_core.view_application"
        ):
            return app
        raise ValidationError(_("User does not have access to application."), code="invalid")

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
