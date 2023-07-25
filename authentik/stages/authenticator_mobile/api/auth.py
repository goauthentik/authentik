"""Mobile device token authentication"""
from typing import Any

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request

from authentik.api.authentication import validate_auth
from authentik.core.models import User
from authentik.stages.authenticator_mobile.models import MobileDeviceToken


class MobileDeviceTokenAuthentication(BaseAuthentication):
    """Mobile device token authentication"""

    def authenticate(self, request: Request) -> tuple[User, Any] | None:
        """Token-based authentication using HTTP Bearer authentication"""
        auth = get_authorization_header(request)
        raw_token = validate_auth(auth)
        device_token: MobileDeviceToken = MobileDeviceToken.objects.filter(token=raw_token).first()
        if not device_token:
            return None

        return (device_token.user, None)


class TokenSchema(OpenApiAuthenticationExtension):
    """Auth schema"""

    target_class = MobileDeviceTokenAuthentication
    name = "mobile_device_token"

    def get_security_definition(self, auto_schema):
        """Auth schema"""
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "scheme": "bearer",
        }
