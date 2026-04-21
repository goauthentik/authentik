"""Account Lockdown Stage API Views"""

from django.urls import reverse_lazy
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
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
)
from authentik.enterprise.api import EnterpriseRequiredMixin, enterprise_action
from authentik.enterprise.stages.account_lockdown.models import AccountLockdownStage
from authentik.enterprise.stages.account_lockdown.stage import (
    QS_LOCKDOWN_USER,
    can_lock_user,
    get_lockdown_target_users,
)
from authentik.flows.api.stages import StageSerializer

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
            "self_service_message_title",
            "self_service_message_body",
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

        The request body selects the target before the flow starts. The
        returned URL carries the same target into the account lockdown stage
        via the ``user_uuid`` query parameter.
        """
        flow = request._request.brand.flow_lockdown
        if not flow:
            raise ValidationError({"non_field_errors": [_("No lockdown flow configured.")]})
        querystring = f"?{urlencode({QS_LOCKDOWN_USER: str(user.pk)})}"
        return request.build_absolute_uri(
            reverse_lazy("authentik_core:if-flow", kwargs={"flow_slug": flow.slug}) + querystring
        )

    @extend_schema(
        description=_(
            "Choose the target account in the request body, then return a flow "
            "URL that passes that target to the account lockdown stage via the "
            "user_uuid query parameter."
        ),
        request=UserAccountLockdownSerializer,
        responses={
            "200": OpenApiResponse(
                response=inline_serializer(
                    "AccountLockdownFlowResponse",
                    {
                        "flow_url": CharField(
                            help_text=_(
                                "URL to redirect to for lockdown flow, including the "
                                "user_uuid query parameter consumed by the stage."
                            )
                        ),
                    },
                ),
                examples=[
                    OpenApiExample(
                        "Lockdown flow URL",
                        value={
                            "flow_url": (
                                "https://example.invalid/if/flow/default-account-lockdown/"
                                "?user_uuid=00000000-0000-0000-0000-000000000000"
                            )
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

        Returns a flow URL for the frontend to redirect to. The returned URL
        includes the ``user_uuid`` query parameter that the lockdown stage uses
        once the flow starts running.
        """
        target_user = body.validated_data.get("user")
        user = target_user if target_user is not None else request.user

        if not can_lock_user(request.user, user):
            LOGGER.debug("Permission denied for account lockdown", user=request.user)
            self.permission_denied(request)

        flow_url = self._create_lockdown_flow_url(request, user)
        LOGGER.debug("Returning lockdown flow URL", flow_url=flow_url, user=user.username)
        return Response({"flow_url": flow_url})
