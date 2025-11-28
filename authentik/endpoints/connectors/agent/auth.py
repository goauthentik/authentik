from typing import Any

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from authentik.api.authentication import IPCUser, validate_auth
from authentik.core.middleware import CTX_AUTH_VIA
from authentik.core.models import User
from authentik.endpoints.connectors.agent.models import DeviceToken, EnrollmentToken


class DeviceUser(IPCUser):
    username = "authentik:endpoints:device"


class AgentEnrollmentAuth(BaseAuthentication):

    def authenticate(self, request: Request) -> tuple[User, Any] | None:
        auth = get_authorization_header(request)
        key = validate_auth(auth)
        token = EnrollmentToken.filter_not_expired(key=key).first()
        if not token:
            raise PermissionDenied()
        CTX_AUTH_VIA.set("endpoint_token_enrollment")
        return (DeviceUser(), token)


class AgentAuth(BaseAuthentication):

    def authenticate(self, request: Request) -> tuple[User, Any] | None:
        auth = get_authorization_header(request)
        key = validate_auth(auth, format="bearer+agent")
        if not key:
            return None
        device_token = DeviceToken.filter_not_expired(key=key).first()
        if not device_token:
            raise PermissionDenied()
        if device_token.device.device.is_expired:
            raise PermissionDenied()
        CTX_AUTH_VIA.set("endpoint_token")
        return (DeviceUser(), device_token)
