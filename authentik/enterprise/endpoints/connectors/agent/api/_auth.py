from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from authentik.core.middleware import CTX_AUTH_VIA
from authentik.enterprise.endpoints.connectors.agent.models import AgentConnector


def authenticate(request: Request) -> AgentConnector:
    auth = get_authorization_header(request).decode()
    auth_type, _, key = auth.partition(" ")
    if auth_type != "Bearer":
        raise PermissionDenied()
    connector = AgentConnector.objects.filter(tokens__key=key).first()
    if not connector:
        raise PermissionDenied()
    CTX_AUTH_VIA.set("endpoint_token")
    return connector
