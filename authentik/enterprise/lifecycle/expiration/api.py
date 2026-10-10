from copy import copy
from uuid import UUID

from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, ChoiceField, DateTimeField, IntegerField, UUIDField
from rest_framework.permissions import IsAuthenticated
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
from authentik.enterprise.lifecycle.offboarding.models import OffboardingAction
from authentik.lib.utils.time import timedelta_from_string
from authentik.rbac.decorators import permission_required

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
            "activity_basis",
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


class UserExpirationRulePendingPreviewSerializer(PassiveSerializer):
    id = UUIDField(read_only=True)
    user = PartialUserSerializer(read_only=True)
    previous_action = ChoiceField(choices=OffboardingAction.choices, read_only=True)
    action = ChoiceField(choices=OffboardingAction.choices, allow_null=True, read_only=True)
    previous_scheduled_at = DateTimeField(read_only=True)
    scheduled_at = DateTimeField(allow_null=True, read_only=True)
    previous_revoke_sessions = BooleanField(read_only=True)
    revoke_sessions = BooleanField(allow_null=True, read_only=True)
    previous_revoke_tokens = BooleanField(read_only=True)
    revoke_tokens = BooleanField(allow_null=True, read_only=True)


class UserExpirationRulePendingPreviewGroupSerializer(PassiveSerializer):
    count = IntegerField(read_only=True)
    offboardings = UserExpirationRulePendingPreviewSerializer(many=True, read_only=True)


class UserExpirationRulePreviewSerializer(PassiveSerializer):
    count = IntegerField(read_only=True)
    users = PartialUserSerializer(many=True, read_only=True)
    updated = UserExpirationRulePendingPreviewGroupSerializer(read_only=True)
    taken_over = UserExpirationRulePendingPreviewGroupSerializer(read_only=True)
    removed = UserExpirationRulePendingPreviewGroupSerializer(read_only=True)


class UserExpirationRuleViewSet(UsedByMixin, ModelViewSet):
    queryset = UserExpirationRule.objects.select_related("group").all()
    serializer_class = UserExpirationRuleSerializer
    search_fields = ["name"]
    ordering = ["name"]
    ordering_fields = ["name", "enabled", "action"]
    filterset_fields = ["enabled", "group", "action", "pbm_uuid"]

    @extend_schema(
        request=UserExpirationRuleSerializer,
        responses={200: UserExpirationRulePreviewSerializer},
    )
    @permission_required("authentik_lifecycle.view_userexpirationrule")
    @action(
        detail=True,
        methods=["GET", "POST"],
        pagination_class=None,
        filter_backends=[],
        permission_classes=[IsAuthenticated],
    )
    def preview(self, request: Request, pk: str) -> Response:
        """Preview new offboardings and changes to pending rows if this rule is enabled.

        POST accepts unsaved edits to the rule. Neither method saves the rule, changes
        offboardings, or sends warnings. Existing policy bindings still apply.
        """
        rule: UserExpirationRule = copy(self.get_object())
        if request.method == "POST":
            serializer = self.get_serializer(rule, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            # Transports affect warning delivery, not qualification or row settings.
            for field, value in serializer.validated_data.items():
                if field not in ("pk", "id", "pbm_uuid", "notification_transports"):
                    setattr(rule, field, value)
        # Preview as if enabled. Keep the rule's identity so its policy bindings
        # still apply.
        rule.enabled = True
        counts = dict.fromkeys(("updated", "taken_over", "removed"), 0)
        offboardings: dict[str, list[dict]] = {change: [] for change in counts}
        withdrawn: list[UUID] = []
        for change, row, due_at in rule.preview_pending():
            counts[change] += 1
            if change == "removed":
                withdrawn.append(row.pk)
            if len(offboardings[change]) >= PREVIEW_LIMIT:
                continue
            offboardings[change].append(
                {
                    "id": row.pk,
                    "user": row.user,
                    "previous_action": row.action,
                    "action": rule.action if due_at is not None else None,
                    "previous_scheduled_at": row.scheduled_at,
                    "scheduled_at": due_at,
                    "previous_revoke_sessions": row.revoke_sessions,
                    "revoke_sessions": rule.revoke_sessions if due_at is not None else None,
                    "previous_revoke_tokens": row.revoke_tokens,
                    "revoke_tokens": rule.revoke_tokens if due_at is not None else None,
                }
            )
        # The sweep withdraws stale owned rows before selecting new candidates. A
        # user may still fall within the warning window and be scheduled again.
        candidates = rule.candidates(withdrawn=withdrawn).order_by("username")
        data: dict[str, object] = {
            "count": candidates.count(),
            "users": PartialUserSerializer(candidates[:PREVIEW_LIMIT], many=True).data,
        }
        data.update(
            {
                change: {"count": count, "offboardings": offboardings[change]}
                for change, count in counts.items()
            }
        )
        return Response(UserExpirationRulePreviewSerializer(data).data)
