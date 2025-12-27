from django.urls import reverse
from django.utils.timezone import now
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from structlog.stdlib import get_logger

from authentik.endpoints.connectors.agent.api.agent import (
    AgentAuthenticationResponse,
    AgentTokenResponseSerializer,
)
from authentik.endpoints.connectors.agent.auth import AgentAuth
from authentik.endpoints.connectors.agent.models import (
    DeviceAuthenticationToken,
    DeviceToken,
)
from authentik.enterprise.endpoints.connectors.agent.auth import (
    DeviceAuthFedAuthentication,
    agent_auth_issue_token,
    check_device_policies,
)
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

LOGGER = get_logger()


class AgentConnectorViewSetMixin:

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses=AgentAuthenticationResponse(),
    )
    @action(methods=["POST"], detail=False, authentication_classes=[AgentAuth])
    def auth_ia(self, request: Request) -> Response:
        token: DeviceToken = request.auth
        auth_token = DeviceAuthenticationToken.objects.create(
            device=token.device.device,
            device_token=token,
            connector=token.device.connector.agentconnector,
        )
        return Response(
            {
                "url": request.build_absolute_uri(
                    reverse(
                        "authentik_enterprise_endpoints_connectors_agent:authenticate",
                        kwargs={"token_uuid": auth_token.identifier},
                    )
                ),
            }
        )

    @extend_schema(
        request=OpenApiTypes.NONE,
        parameters=[OpenApiParameter("device", OpenApiTypes.STR, location="query", required=True)],
        responses={
            200: AgentTokenResponseSerializer(),
            404: OpenApiResponse(description="Device not found"),
        },
    )
    @action(
        methods=["POST"],
        detail=False,
        pagination_class=None,
        filter_backends=[],
        permission_classes=[IsAuthenticated],
        authentication_classes=[DeviceAuthFedAuthentication],
    )
    def auth_fed(self, request: Request) -> Response:
        federated_token, device, connector = request.auth

        policy_result = check_device_policies(device, federated_token.user, request._request)
        if not policy_result.passing:
            raise ValidationError(
                {"policy_result": "Policy denied access", "policy_messages": policy_result.messages}
            )

        token, exp = agent_auth_issue_token(device, connector, federated_token.user)
        rel_exp = int((exp - now()).total_seconds())
        Event.new(
            EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "jwt",
                PLAN_CONTEXT_METHOD_ARGS: {
                    "jwt": federated_token,
                    "provider": federated_token.provider,
                },
                PLAN_CONTEXT_DEVICE: device,
            },
        ).from_http(request, user=federated_token.user)
        return Response({"token": token, "expires_in": rel_exp})
