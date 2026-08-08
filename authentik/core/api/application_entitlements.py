"""Application Roles API Viewset"""

from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField
from rest_framework.request import Request
from rest_framework.response import Response
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
    filterset_fields = [
        "pbm_uuid",
        "name",
        "app",
    ]
    ordering = ["app__name", "name"]
    ordering_fields = ["name", "app__name"]

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        queryset = super().filter_queryset(queryset)
        for_user_pk = self.request.query_params.get("for_user")
        if for_user_pk is None:
            return queryset
        try:
            for_user_pk = int(for_user_pk)
        except ValueError:
            raise ValidationError({"for_user": "for_user must be numerical"}) from None
        for_user: User | None = (
            get_objects_for_user(self.request.user, "authentik_core.view_user_applications")
            .filter(pk=for_user_pk)
            .first()
        )
        if not for_user:
            raise ValidationError({"for_user": "User not found"})
        return queryset.filter(
            pbm_uuid__in=for_user.all_app_entitlements().values_list("pbm_uuid", flat=True)
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="for_user",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
            )
        ]
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        """List application entitlements, optionally scoped to a user via `for_user`."""
        return super().list(request, *args, **kwargs)
