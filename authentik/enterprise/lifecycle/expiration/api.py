from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import PartialGroupSerializer
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import UserTypes
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.lifecycle.expiration.models import UserExpirationRule
from authentik.lib.utils.time import timedelta_from_string

PREVIEW_LIMIT = 20


class UserExpirationRuleSerializer(EnterpriseRequiredMixin, ModelSerializer):
    group_obj = PartialGroupSerializer(source="group", read_only=True)

    class Meta:
        model = UserExpirationRule
        fields = [
            "pk",
            "pbm_uuid",
            "name",
            "enabled",
            "group",
            "group_obj",
            "user_types",
            "inactivity_duration",
            "action",
            "revoke_sessions",
            "revoke_tokens",
            "warn_before",
            "notification_transports",
            "exclude_superusers",
            "policy_engine_mode",
        ]

    def validate_user_types(self, value: list[str]) -> list[str]:
        if UserTypes.INTERNAL_SERVICE_ACCOUNT in value:
            raise ValidationError(_("Internal service accounts cannot be expired."))
        return value

    def validate_warn_before(self, value: str | None) -> str | None:
        return value or None

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        duration = attrs.get(
            "inactivity_duration",
            getattr(
                self.instance,
                "inactivity_duration",
                UserExpirationRule._meta.get_field("inactivity_duration").get_default(),
            ),
        )
        warn_before = attrs.get("warn_before", getattr(self.instance, "warn_before", None))
        if (
            duration
            and warn_before
            and timedelta_from_string(warn_before) >= timedelta_from_string(duration)
        ):
            raise ValidationError(
                {"warn_before": _("Warning period must be shorter than the inactivity duration.")}
            )
        return attrs


class UserExpirationRulePreviewSerializer(PassiveSerializer):
    count = IntegerField(read_only=True)
    users = PartialUserSerializer(many=True, read_only=True)


class UserExpirationRuleViewSet(UsedByMixin, ModelViewSet):
    queryset = UserExpirationRule.objects.select_related("group").all()
    serializer_class = UserExpirationRuleSerializer
    search_fields = ["name"]
    ordering = ["name"]
    ordering_fields = ["name", "enabled", "action"]
    filterset_fields = ["enabled", "group", "action", "pbm_uuid"]

    @extend_schema(responses={200: UserExpirationRulePreviewSerializer})
    @action(detail=True, methods=["GET"], pagination_class=None, filter_backends=[])
    def preview(self, request: Request, pk: str) -> Response:
        """Users the next sweep of this rule would schedule an offboarding for."""
        rule: UserExpirationRule = self.get_object()
        candidates = rule.candidates().order_by("username")
        data = {
            "count": candidates.count(),
            "users": PartialUserSerializer(candidates[:PREVIEW_LIMIT], many=True).data,
        }
        return Response(UserExpirationRulePreviewSerializer(data).data)
