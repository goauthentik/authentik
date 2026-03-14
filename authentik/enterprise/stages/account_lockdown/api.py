"""Account Lockdown Stage API Views"""

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse_lazy
from django.utils.http import urlencode
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
from authentik.core.models import (
    User,
    UserTypes,
    default_token_duration,
)
from authentik.enterprise.api import EnterpriseRequiredMixin, enterprise_action
from authentik.enterprise.stages.account_lockdown.models import AccountLockdownStage
from authentik.flows.api.stages import StageSerializer
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, FlowAuthenticationRequirement, FlowToken
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


class UserAccountLockdownMixin:
    """Enterprise account-lockdown API actions for UserViewSet."""

    def _get_lockdown_flow(self, request: Request) -> Flow:
        flow = request._request.brand.flow_lockdown
        if not flow:
            raise ValidationError({"non_field_errors": [_("No lockdown flow configured.")]})
        return flow

    def _build_flow_url(self, request: Request, flow: Flow, token: FlowToken | None = None) -> str:
        querystring = f"?{urlencode({QS_KEY_TOKEN: token.key})}" if token else ""
        return request.build_absolute_uri(
            reverse_lazy("authentik_core:if-flow", kwargs={"flow_slug": flow.slug}) + querystring
        )

    def _plan_lockdown_flow(self, request: Request, flow: Flow, user: User) -> FlowToken:
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        original_user = request._request.user
        request._request.user = AnonymousUser()
        try:
            plan = planner.plan(
                request._request,
                {
                    PLAN_CONTEXT_PENDING_USER: user,
                },
            )
        except FlowNonApplicableException as exc:
            raise ValidationError(
                {"non_field_errors": [_("Lockdown flow not applicable to user.")]}
            ) from exc
        finally:
            request._request.user = original_user

        token, __ = FlowToken.objects.update_or_create(
            identifier=f"{user.uid}-account-lockdown",
            defaults={
                "user": user,
                "flow": flow,
                "_plan": FlowToken.pickle(plan),
                "revoke_on_execution": True,
                "expires": default_token_duration(),
                "expiring": True,
            },
        )
        return token

    def _create_lockdown_flow_url(self, request: Request, user: User, self_service: bool) -> str:
        """Create a flow URL for account lockdown."""
        flow = self._get_lockdown_flow(request)

        if self_service:
            planner = FlowPlanner(flow)
            planner.allow_empty_flows = True
            try:
                planner.plan(
                    request._request,
                    {
                        PLAN_CONTEXT_PENDING_USER: request.user,
                    },
                )
            except FlowNonApplicableException as exc:
                raise ValidationError(
                    {"non_field_errors": [_("Lockdown flow not applicable to user.")]}
                ) from exc
            return self._build_flow_url(request, flow)

        token = self._plan_lockdown_flow(request, flow, user)
        return self._build_flow_url(request, flow, token)

    @extend_schema(
        request=UserAccountLockdownSerializer,
        responses={
            "200": inline_serializer(
                "AccountLockdownFlowResponse",
                {
                    "flow_url": CharField(help_text="URL to redirect to for lockdown flow"),
                },
            ),
            "400": OpenApiResponse(
                description="No lockdown flow configured or the flow is not applicable"
            ),
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

        Returns a flow URL for the frontend to redirect to.
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
        LOGGER.debug("Returning lockdown flow URL", flow_url=flow_url, user=user.username)
        return Response({"flow_url": flow_url})
