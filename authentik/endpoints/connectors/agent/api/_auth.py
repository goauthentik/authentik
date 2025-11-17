from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from authentik.core.middleware import CTX_AUTH_VIA
from authentik.endpoints.connectors.agent.models import AgentConnector, DeviceToken, EnrollmentToken


def authenticate_enrollment(request: Request) -> AgentConnector:
    auth = get_authorization_header(request).decode()
    auth_type, _, key = auth.partition(" ")
    if auth_type != "Bearer":
        raise PermissionDenied()
    token = EnrollmentToken.filter_not_expired(key=key).first()
    if not token:
        raise PermissionDenied()
    CTX_AUTH_VIA.set("endpoint_token_enrollment")
    return token.connector


def authenticate_device(request: Request) -> DeviceToken:
    auth = get_authorization_header(request).decode()
    auth_type, _, key = auth.partition(" ")
    if auth_type != "Bearer":
        raise PermissionDenied()
    connection = DeviceToken.filter_not_expired(key=key).first()
    if not connection:
        raise PermissionDenied()
    if connection.device.device.is_expired:
        raise PermissionDenied()
    CTX_AUTH_VIA.set("endpoint_token")
    return connection
