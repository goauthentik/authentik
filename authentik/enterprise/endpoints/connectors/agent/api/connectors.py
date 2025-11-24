from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
)
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.endpoints.connectors.agent.api.agent import (
    AgentAuthenticationResponse,
    PassiveSerializer,
)
from authentik.endpoints.connectors.agent.auth import (
    AgentAuth,
)
from authentik.endpoints.connectors.agent.models import (
    AuthenticationToken,
    DeviceToken,
)
from authentik.lib.generators import generate_id


class AgentAuthValidate(PassiveSerializer):

    token = CharField()


class AgentConnectorViewSetMixin:

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses=AgentAuthenticationResponse(),
    )
    @action(methods=["POST"], detail=False, authentication_classes=[AgentAuth])
    def auth_ia(self, request: Request) -> Response:
        token: DeviceToken = request.auth
        auth_token = AuthenticationToken.objects.create(
            device=token.device.device,
            connector=token.device.connector,
        )
        return Response(
            {
                "url": request.build_absolute_uri(
                    reverse(
                        "authentik_enterprise_endpoints_connectors_agent:authenticate",
                        kwargs={"token_uuid": auth_token.identifier},
                    )
                ),
                "nonce": generate_id(),
            }
        )

    @action(methods=["POST"], detail=False)
    def auth_fed(self, request: Request) -> Response:
        pass
