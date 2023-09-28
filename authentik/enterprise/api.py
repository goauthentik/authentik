"""Enterprise API Views"""
from datetime import datetime, timedelta

from django.utils.timezone import now
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, DateTimeField, IntegerField
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.api.decorators import permission_required
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User, UserTypes
from authentik.enterprise.models import License, LicenseKey
from authentik.root.install_id import get_install_id


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


class LicenseSummary(PassiveSerializer):
    """Serializer for license status"""

    internal_users = IntegerField(required=True)
    external_users = IntegerField(required=True)
    valid = BooleanField()
    show_admin_warning = BooleanField()
    show_user_warning = BooleanField()
    read_only = BooleanField()
    latest_valid = DateTimeField()
    has_license = BooleanField()


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
    @action(detail=False, methods=["GET"], permission_classes=[IsAdminUser])
    def get_install_id(self, request: Request) -> Response:
        """Get install_id"""
        return Response(
            data={
                "install_id": get_install_id(),
            }
        )

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            200: LicenseSummary(),
        },
    )
    @action(detail=False, methods=["GET"], permission_classes=[IsAuthenticated])
    def summary(self, request: Request) -> Response:
        """Get the total license status"""
        total = LicenseKey.get_total()
        last_valid = LicenseKey.last_valid_date()
        # TODO: move this to a different place?
        show_admin_warning = last_valid < now() - timedelta(weeks=2)
        show_user_warning = last_valid < now() - timedelta(weeks=4)
        read_only = last_valid < now() - timedelta(weeks=6)
        latest_valid = datetime.fromtimestamp(total.exp)
        response = LicenseSummary(
            data={
                "internal_users": total.internal_users,
                "external_users": total.external_users,
                "valid": total.is_valid(),
                "show_admin_warning": show_admin_warning,
                "show_user_warning": show_user_warning,
                "read_only": read_only,
                "latest_valid": latest_valid,
                "has_license": License.objects.all().count() > 0,
            }
        )
        response.is_valid(raise_exception=True)
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
                "internal_users": LicenseKey.get_default_user_count(),
                "external_users": LicenseKey.get_external_user_count(),
                "forecasted_internal_users": (internal_in_last_month * forecast_for_months),
                "forecasted_external_users": (external_in_last_month * forecast_for_months),
            }
        )
        response.is_valid(raise_exception=True)
        return Response(response.data)
