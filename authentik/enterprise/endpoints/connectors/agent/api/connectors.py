from urllib.parse import urlencode

from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.endpoints.connectors.agent.api.agent import AgentAuthenticationResponse
from authentik.endpoints.connectors.agent.auth import AgentAuth
from authentik.endpoints.connectors.agent.models import (
    DeviceAuthenticationToken,
    DeviceToken,
)
from authentik.enterprise.api import enterprise_action

LOGGER = get_logger()


class AgentConnectorViewSetMixin:

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses=AgentAuthenticationResponse(),
        parameters=[OpenApiParameter(QS_LOGIN_HINT, type=OpenApiTypes.STR, required=False)],
    )
    @action(
        methods=["POST"],
        detail=False,
        authentication_classes=[AgentAuth],
        # Permissions are handled via AgentAuth
        permission_classes=[IsAuthenticated],
    )
    @enterprise_action
    def auth_ia(self, request: Request) -> Response:
        token: DeviceToken = request.auth
        auth_token = DeviceAuthenticationToken.objects.create(
            device=token.device.device,
            device_token=token,
            connector=token.device.connector.agentconnector,
        )
        final_url = request.build_absolute_uri(
            reverse(
                "authentik_enterprise_endpoints_connectors_agent:authenticate",
                kwargs={"token_uuid": auth_token.identifier},
            )
        )
        if hint := request.query_params.get(QS_LOGIN_HINT):
            final_url += "?" + urlencode({QS_LOGIN_HINT: hint})
        return Response({"url": final_url})
