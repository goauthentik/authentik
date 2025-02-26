"""Enterprise API Views"""

from datetime import timedelta

from django.utils.timezone import now
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, IntegerField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import User, UserTypes
from authentik.enterprise.license import LicenseKey, LicenseSummarySerializer
from authentik.enterprise.models import License
from authentik.rbac.decorators import permission_required
from authentik.tenants.utils import get_unique_identifier


class EnterpriseRequiredMixin:
    """Mixin to validate that a valid enterprise license
    exists before allowing to save the object"""

    def validate(self, attrs: dict) -> dict:
        """Check that a valid license exists"""
        if not LicenseKey.cached_summary().status.is_valid:
            raise ValidationError(_("Enterprise is required to create/update this object."))
        return super().validate(attrs)


class LicenseSerializer(ModelSerializer):
    """License Serializer"""

    def validate_key(self, key: str) -> str:
        """Validate the license key (install_id and signature)"""
        LicenseKey.validate(key)
        return key

    class Meta:
        model = License
        fields = [
            "license_uuid",
            "name",
            "key",
            "expiry",
            "internal_users",
            "external_users",
        ]
        extra_kwargs = {
            "name": {"read_only": True},
            "expiry": {"read_only": True},
            "internal_users": {"read_only": True},
            "external_users": {"read_only": True},
        }


class LicenseForecastSerializer(PassiveSerializer):
    """Serializer for license forecast"""

    internal_users = IntegerField(required=True)
    external_users = IntegerField(required=True)
    forecasted_internal_users = IntegerField(required=True)
    forecasted_external_users = IntegerField(required=True)


class LicenseViewSet(UsedByMixin, ModelViewSet):
    """License Viewset"""

    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    search_fields = ["name"]
    ordering = ["name"]
    filterset_fields = ["name"]

    @permission_required(None, ["authentik_enterprise.view_license"])
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            200: inline_serializer("InstallIDSerializer", {"install_id": CharField(required=True)}),
        },
    )
    @action(detail=False, methods=["GET"])
    def install_id(self, request: Request) -> Response:
        """Get install_id"""
        return Response(
            data={
                "install_id": get_unique_identifier(),
            }
        )

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            200: LicenseSummarySerializer(),
        },
        parameters=[
            OpenApiParameter(
                name="cached",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                default=True,
            )
        ],
    )
    @action(detail=False, methods=["GET"], permission_classes=[IsAuthenticated])
    def summary(self, request: Request) -> Response:
        """Get the total license status"""
        summary = LicenseKey.cached_summary()
        if request.query_params.get("cached", "true").lower() == "false":
            summary = LicenseKey.get_total().summary()
        response = LicenseSummarySerializer(instance=summary)
        return Response(response.data)

    @permission_required(None, ["authentik_enterprise.view_license"])
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            200: LicenseForecastSerializer(),
        },
    )
    @action(detail=False, methods=["GET"])
    def forecast(self, request: Request) -> Response:
        """Forecast how many users will be required in a year"""
        last_month = now() - timedelta(days=30)
        # Forecast for internal users
        internal_in_last_month = User.objects.filter(
            type=UserTypes.INTERNAL, date_joined__gte=last_month
        ).count()
        # Forecast for external users
        external_in_last_month = LicenseKey.get_external_user_count()
        forecast_for_months = 12
        response = LicenseForecastSerializer(
            data={
                "internal_users": LicenseKey.get_internal_user_count(),
                "external_users": LicenseKey.get_external_user_count(),
                "forecasted_internal_users": (internal_in_last_month * forecast_for_months),
                "forecasted_external_users": (external_in_last_month * forecast_for_months),
            }
        )
        response.is_valid(raise_exception=True)
        return Response(response.data)
