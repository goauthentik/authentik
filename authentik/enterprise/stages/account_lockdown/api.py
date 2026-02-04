"""Account Lockdown Stage API Views"""

from hashlib import sha256

from django.urls import reverse_lazy
from django.utils.http import urlencode
from django.utils.text import slugify
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.validation import validate
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User, UserTypes
from authentik.enterprise.api import EnterpriseRequiredMixin, enterprise_action
from authentik.enterprise.stages.account_lockdown.models import (
    PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE,
    PLAN_CONTEXT_LOCKDOWN_TARGET,
    PLAN_CONTEXT_LOCKDOWN_TARGETS,
    AccountLockdownStage,
)
from authentik.flows.api.stages import StageSerializer
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import FlowAuthenticationRequirement, FlowToken
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from authentik.flows.views.executor import QS_KEY_TOKEN

LOGGER = get_logger()


class AccountLockdownStageSerializer(EnterpriseRequiredMixin, StageSerializer):
    """AccountLockdownStage Serializer"""

    def validate_self_service_completion_flow(self, flow):
        if flow and flow.authentication != FlowAuthenticationRequirement.NONE:
            raise ValidationError(
                "Completion flow must not require authentication for self-service lockdown."
            )
        return flow

    class Meta:
        model = AccountLockdownStage
        fields = StageSerializer.Meta.fields + [
            "deactivate_user",
            "set_unusable_password",
            "delete_sessions",
            "revoke_tokens",
            "self_service_message_title",
            "self_service_message",
            "self_service_completion_flow",
        ]


class AccountLockdownStageViewSet(UsedByMixin, ModelViewSet):
    """AccountLockdownStage Viewset"""

    queryset = AccountLockdownStage.objects.all()
    serializer_class = AccountLockdownStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]


class UserAccountLockdownSerializer(PassiveSerializer):
    """Payload to trigger account lockdown for a user"""

    user = PrimaryKeyRelatedField(
        queryset=User.objects.all()
        .exclude_anonymous()
        .exclude(type=UserTypes.INTERNAL_SERVICE_ACCOUNT),
        required=False,
        allow_null=True,
        help_text="User to lock. If omitted, locks the current user (self-service).",
    )


class UserBulkAccountLockdownSerializer(PassiveSerializer):
    """Payload to trigger account lockdown for multiple users"""

    users = PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all()
        .exclude_anonymous()
        .exclude(type=UserTypes.INTERNAL_SERVICE_ACCOUNT),
        help_text="Users to lock",
    )

    def validate_users(self, users: list[User]) -> list[User]:
        if not users:
            raise ValidationError("At least one user is required.")
        seen: set[int] = set()
        unique_users: list[User] = []
        for user in users:
            if user.pk in seen:
                continue
            seen.add(user.pk)
            unique_users.append(user)
        return unique_users


class UserAccountLockdownMixin:
    """Enterprise account-lockdown API actions for UserViewSet."""

    def _create_lockdown_flow_url(
        self, request: Request, user: User, self_service: bool
    ) -> str | None:
        """Create a flow URL for account lockdown if a lockdown flow is configured."""
        brand = request._request.brand
        flow = brand.flow_lockdown
        if not flow:
            return None

        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                request._request,
                {
                    PLAN_CONTEXT_LOCKDOWN_TARGET: user,
                    PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE: self_service,
                    PLAN_CONTEXT_PENDING_USER: user,
                },
            )
        except FlowNonApplicableException:
            LOGGER.debug("Lockdown flow not applicable", flow=flow.slug)
            return None

        token, __ = FlowToken.objects.update_or_create(
            identifier=slugify(f"ak-lockdown-{user.uid}"),
            defaults={
                "user": request.user,
                "flow": flow,
                "_plan": FlowToken.pickle(plan),
            },
        )
        querystring = urlencode({QS_KEY_TOKEN: token.key})
        return request.build_absolute_uri(
            reverse_lazy("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
            + f"?{querystring}"
        )

    def _create_lockdown_flow_url_bulk(self, request: Request, users: list[User]) -> str | None:
        """Create a flow URL for bulk account lockdown if a lockdown flow is configured."""
        brand = request._request.brand
        flow = brand.flow_lockdown
        if not flow:
            return None

        # If the actor is in the target list, treat this as self-service too so
        # the stage can use the safe self-service completion path after sessions are revoked.
        self_service = any(user.pk == request.user.pk for user in users)

        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                request._request,
                {
                    PLAN_CONTEXT_LOCKDOWN_TARGETS: users,
                    PLAN_CONTEXT_LOCKDOWN_SELF_SERVICE: self_service,
                },
            )
        except FlowNonApplicableException:
            LOGGER.debug("Lockdown flow not applicable", flow=flow.slug)
            return None

        # Use a stable hash so different selections don't collide.
        user_ids = ",".join(str(u.pk) for u in users)
        digest = sha256(user_ids.encode("utf-8")).hexdigest()[:12]
        token, __ = FlowToken.objects.update_or_create(
            identifier=slugify(f"ak-lockdown-bulk-{digest}"),
            defaults={
                "user": request.user,
                "flow": flow,
                "_plan": FlowToken.pickle(plan),
            },
        )
        querystring = urlencode({QS_KEY_TOKEN: token.key})
        return request.build_absolute_uri(
            reverse_lazy("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
            + f"?{querystring}"
        )

    @extend_schema(
        request=UserAccountLockdownSerializer,
        responses={
            "200": inline_serializer(
                "AccountLockdownFlowResponse",
                {
                    "flow_url": CharField(help_text="URL to redirect to for lockdown flow"),
                },
            ),
            "400": OpenApiResponse(description="No lockdown flow configured or invalid target"),
            "403": OpenApiResponse(description="Permission denied (when targeting another user)"),
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
        url_path="account_lockdown",
    )
    @validate(UserAccountLockdownSerializer)
    @enterprise_action
    def account_lockdown(self, request: Request, body: UserAccountLockdownSerializer) -> Response:
        """Trigger account lockdown for a user.

        If no user is specified, locks the current user (self-service).
        When targeting another user, admin permissions are required.

        A lockdown flow must be configured on the brand. Returns a flow URL for the frontend
        to redirect to.
        """
        target_user = body.validated_data.get("user")
        self_service = target_user is None or target_user.pk == request.user.pk

        if self_service:
            user = request.user
        else:
            user = target_user
            perm = "authentik_core.change_user"
            if not request.user.has_perm(perm) and not request.user.has_perm(perm, user):
                LOGGER.debug("Permission denied for account lockdown", user=request.user, perm=perm)
                self.permission_denied(request)

        flow_url = self._create_lockdown_flow_url(request, user, self_service)
        if not flow_url:
            raise ValidationError({"non_field_errors": [_("No lockdown flow configured.")]})

        LOGGER.debug("Returning lockdown flow URL", flow_url=flow_url, user=user.username)
        return Response({"flow_url": flow_url})

    @extend_schema(
        request=UserBulkAccountLockdownSerializer,
        responses={
            "200": inline_serializer(
                "AccountLockdownBulkFlowResponse",
                {
                    "flow_url": CharField(help_text="URL to redirect to for lockdown flow"),
                },
            ),
            "400": OpenApiResponse(description="No lockdown flow configured"),
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
        url_path="account_lockdown_bulk",
    )
    @validate(UserBulkAccountLockdownSerializer)
    @enterprise_action
    def account_lockdown_bulk(
        self, request: Request, body: UserBulkAccountLockdownSerializer
    ) -> Response:
        """Trigger account lockdown for multiple users.

        A lockdown flow must be configured on the brand. Returns a flow URL for the frontend
        to redirect to.
        """
        users = body.validated_data["users"]
        perm = "authentik_core.change_user"
        if not request.user.has_perm(perm):
            for user in users:
                if not request.user.has_perm(perm, user):
                    LOGGER.debug(
                        "Permission denied for bulk account lockdown",
                        user=request.user,
                        perm=perm,
                    )
                    self.permission_denied(request)

        flow_url = self._create_lockdown_flow_url_bulk(request, users)
        if not flow_url:
            raise ValidationError({"non_field_errors": [_("No lockdown flow configured.")]})

        return Response({"flow_url": flow_url})
