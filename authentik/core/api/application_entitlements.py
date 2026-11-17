"""Application Roles API Viewset"""

from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet, ModelChoiceFilter
from drf_spectacular.utils import extend_schema_field
from guardian.shortcuts import get_objects_for_user
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField
from rest_framework.viewsets import ModelViewSet

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.object_attributes import AttributesMixinSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import (
    Application,
    ApplicationEntitlement,
    User,
)
from authentik.lib.utils.reflection import ConditionalInheritance


class ApplicationEntitlementSerializer(AttributesMixinSerializer, ModelSerializer):
    """ApplicationEntitlement Serializer"""

    app_name = ReadOnlyField(source="app.name")
    app_slug = ReadOnlyField(source="app.slug")

    def validate_app(self, app: Application) -> Application:
        """Ensure user has permission to view"""
        request: HttpRequest = self.context.get("request")
        if not request and SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            return app
        user = request.user
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
            "app_name",
            "app_slug",
            "attributes",
        ]


class ApplicationEntitlementFilter(FilterSet):
    """Filter for application entitlements"""

    for_user = ModelChoiceFilter(
        queryset=User.objects.all(),
        method="filter_for_user",
    )

    @extend_schema_field(
        {
            "type": "integer",
            "description": _(
                "Entitlements assigned to this user, directly or through a group, "
                "regardless of the user's access to the application."
            ),
        }
    )
    def filter_for_user(
        self, queryset: QuerySet[ApplicationEntitlement], name, value: User
    ) -> QuerySet[ApplicationEntitlement]:
        if (
            not get_objects_for_user(self.request.user, "authentik_core.view_user_applications")
            .filter(pk=value.pk)
            .exists()
        ):
            raise ValidationError({"for_user": "User not found"})
        return queryset.filter(pk__in=value.all_app_entitlements().values("pk"))

    class Meta:
        model = ApplicationEntitlement
        fields = [
            "pbm_uuid",
            "name",
            "app",
            "for_user",
        ]


class ApplicationEntitlementViewSet(
    ConditionalInheritance(
        "authentik.enterprise.requests.api.apps.ApplicationEntitlementsRequestableMixin"
    ),
    UsedByMixin,
    ModelViewSet,
):
    """ApplicationEntitlement Viewset"""

    queryset = ApplicationEntitlement.objects.select_related("app").all()
    serializer_class = ApplicationEntitlementSerializer
    search_fields = [
        "pbm_uuid",
        "name",
        "app__name",
        "app__slug",
        "attributes",
    ]
    filterset_class = ApplicationEntitlementFilter
    ordering = ["app__name", "name"]
    ordering_fields = ["name", "app__name"]
