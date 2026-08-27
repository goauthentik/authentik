"""Account Lockdown Stage API Views"""

from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.validation import validate
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import LinkSerializer, PassiveSerializer
from authentik.core.models import (
    User,
)
from authentik.enterprise.api import EnterpriseRequiredMixin, enterprise_action
from authentik.enterprise.stages.account_lockdown.models import AccountLockdownStage
from authentik.enterprise.stages.account_lockdown.stage import (
    can_lock_user,
    get_lockdown_target_users,
)
from authentik.flows.api.stages import StageSerializer
from authentik.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner

LOGGER = get_logger()


class AccountLockdownStageSerializer(EnterpriseRequiredMixin, StageSerializer):
    """AccountLockdownStage Serializer"""

    class Meta:
        model = AccountLockdownStage
        fields = StageSerializer.Meta.fields + [
            "deactivate_user",
            "set_unusable_password",
            "delete_sessions",
            "revoke_tokens",
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
    """Choose the target account before starting the lockdown flow."""

    user = PrimaryKeyRelatedField(
        queryset=get_lockdown_target_users(),
        required=False,
        allow_null=True,
        help_text=_("User to lock. If omitted, locks the current user (self-service)."),
    )


class UserAccountLockdownMixin:
    """Enterprise account-lockdown API actions for UserViewSet."""

    def _create_lockdown_flow_url(self, request: Request, user: User) -> str:
        """Create a flow URL for account lockdown.

        The request body selects the target before the flow starts. The API
        pre-plans the lockdown flow with the target as the pending user, so the
        account lockdown stage can use the normal flow context.
        """
        flow = request._request.brand.flow_lockdown
        if flow is None:
            raise ValidationError({"non_field_errors": [_("No lockdown flow configured.")]})
        planner = FlowPlanner(flow)
        planner.use_cache = False
        try:
            plan = planner.plan(request._request, {PLAN_CONTEXT_PENDING_USER: user})
        except EmptyFlowException, FlowNonApplicableException:
            raise ValidationError(
                {"non_field_errors": [_("Lockdown flow is not applicable.")]}
            ) from None
        return plan.to_redirect(request._request, flow).url

    @extend_schema(
        description=_("Choose the target account, then return a flow link."),
        request=UserAccountLockdownSerializer,
        responses={
            "200": OpenApiResponse(
                response=LinkSerializer,
                examples=[
                    OpenApiExample(
                        "Lockdown flow URL",
                        value={
                            "link": "https://example.invalid/if/flow/default-account-lockdown/",
                        },
                        response_only=True,
                        status_codes=["200"],
                    )
                ],
            ),
            "400": OpenApiResponse(
                description=_("No lockdown flow configured or the flow is not applicable")
            ),
            "403": OpenApiResponse(
                description=_("Permission denied (when targeting another user)")
            ),
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

        Returns a flow link for the frontend to follow. The flow is pre-planned
        with the target user as pending user for the lockdown stage.
        """
        user = body.validated_data.get("user") or request.user

        if not can_lock_user(request.user, user):
            LOGGER.debug("Permission denied for account lockdown", user=request.user)
            self.permission_denied(request)

        flow_url = self._create_lockdown_flow_url(request, user)
        LOGGER.debug("Returning lockdown flow URL", flow_url=flow_url, user=user.username)
        return Response({"link": flow_url})
