"""Enterprise API Views"""

from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps

from django.db.models import Count, Q
from django.utils.timezone import now
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, DateTimeField, IntegerField, ListField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet

from authentik.api.validation import validate
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import User, UserTypes
from authentik.enterprise.license import LicenseKey, LicenseSummarySerializer
from authentik.enterprise.models import License
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
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


def enterprise_action(func: Callable):
    """Check permissions for a single custom action"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Response:
        if not LicenseKey.cached_summary().status.is_valid:
            raise ValidationError(_("Enterprise is required to use this endpoint."))
        return func(*args, **kwargs)

    return wrapper


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
            "key": {"validators": [UniqueValidator(queryset=License.objects.all())]},
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


class LicenseUserCountsParameters(PassiveSerializer):
    """Parameters for active user counts."""

    count_steps = ListField(
        child=CharField(validators=[timedelta_string_validator]),
        required=False,
        max_length=20,
        help_text="Positive relative periods, such as 'days=30' or 'weeks=3;days=2'.",
    )
    start = DateTimeField(
        required=False,
        help_text="Inclusive start of an absolute range; must be provided with end.",
    )
    end = DateTimeField(
        required=False,
        help_text="Exclusive end of an absolute range; must be provided with start.",
    )

    def validate_count_steps(self, value: list[str]) -> list[str]:
        """Ensure relative periods have a positive duration."""
        for step in value:
            if timedelta_from_string(step) <= timedelta(0):
                raise ValidationError(_("Count steps must have a positive duration."))
        return value

    def validate(self, attrs: dict) -> dict:
        """Require relative periods or a valid absolute range."""
        has_start = "start" in attrs
        has_end = "end" in attrs
        if has_start != has_end:
            raise ValidationError(_("Start and end must be specified together."))
        if has_start and attrs["start"] >= attrs["end"]:
            raise ValidationError(_("Start must be earlier than end."))
        if not attrs.get("count_steps") and not has_start:
            raise ValidationError(_("Specify at least one count step or an absolute range."))
        return attrs


class LicenseUserCountRangeSerializer(PassiveSerializer):
    """Counts of active users added within a date range."""

    start = DateTimeField(required=True)
    end = DateTimeField(required=True)
    interval = CharField(required=True, allow_null=True)
    internal_users_added = IntegerField(required=True)
    external_users_added = IntegerField(required=True)


class LicenseUserCountsSerializer(PassiveSerializer):
    """Current active user totals and counts for requested date ranges."""

    active_internal_users = IntegerField(required=True)
    active_external_users = IntegerField(required=True)
    ranges = LicenseUserCountRangeSerializer(many=True, required=True)


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

    @permission_required(None, ["authentik_enterprise.view_license"])
    @extend_schema(
        request=OpenApiTypes.NONE,
        parameters=[LicenseUserCountsParameters],
        responses={200: LicenseUserCountsSerializer()},
    )
    @action(detail=False, methods=["GET"], pagination_class=None)
    @validate(LicenseUserCountsParameters, "query")
    def user_counts(
        self, request: Request, query: LicenseUserCountsParameters
    ) -> Response:
        """Get active user totals and counts for relative or absolute date ranges.

        At least one positive relative count step or a complete absolute range is required.
        Relative and absolute ranges may be combined. Range starts are inclusive and ends are
        exclusive. Counts include currently active, non-anonymous accounts.
        """
        current_time = now()
        ranges: list[tuple[str | None, datetime, datetime]] = []
        for step in query.validated_data.get("count_steps", []):
            ranges.append((step, current_time - timedelta_from_string(step), current_time))
        if "start" in query.validated_data:
            ranges.append(
                (
                    None,
                    query.validated_data["start"],
                    query.validated_data["end"],
                )
            )

        aggregations = {
            "active_internal_users": Count("pk", filter=Q(type=UserTypes.INTERNAL)),
            "active_external_users": Count("pk", filter=Q(type=UserTypes.EXTERNAL)),
        }
        for index, (_interval, start, end) in enumerate(ranges):
            for user_type in (UserTypes.INTERNAL, UserTypes.EXTERNAL):
                aggregations[f"{user_type}_{index}"] = Count(
                    "pk",
                    filter=Q(type=user_type, date_joined__gte=start, date_joined__lt=end),
                )
        counts = LicenseKey.base_user_qs().aggregate(**aggregations)
        response = LicenseUserCountsSerializer(
            data={
                "active_internal_users": counts["active_internal_users"],
                "active_external_users": counts["active_external_users"],
                "ranges": [
                    {
                        "interval": interval,
                        "start": start,
                        "end": end,
                        "internal_users_added": counts[f"{UserTypes.INTERNAL}_{index}"],
                        "external_users_added": counts[f"{UserTypes.EXTERNAL}_{index}"],
                    }
                    for index, (interval, start, end) in enumerate(ranges)
                ],
            }
        )
        response.is_valid(raise_exception=True)
        return Response(response.data)
