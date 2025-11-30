from typing import Any

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from jwt import PyJWTError, decode, encode, get_unverified_header
from rest_framework.exceptions import ValidationError
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, Session, User
from authentik.core.sessions import SessionStore
from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    AgentDeviceUserBinding,
    AppleNonce,
    DeviceAuthenticationToken,
)
from authentik.enterprise.endpoints.connectors.agent.http import JWEResponse
from authentik.events.models import Event, EventAction
from authentik.events.signals import SESSION_LOGIN_EVENT
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.constants import TOKEN_TYPE
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import JWTAlgorithms
from authentik.root.middleware import SessionMiddleware

LOGGER = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(View):

    device_connection: AgentDeviceConnection
    connector: AgentConnector

    def post(self, request: HttpRequest) -> HttpResponse:
        assertion = request.POST.get("assertion", request.POST.get("request"))
        if not assertion:
            return HttpResponse(status=400)
        self.now = now()
        try:
            self.jwt_request = self.validate_request_token(assertion)
        except PyJWTError as exc:
            LOGGER.warning("failed to parse JWT", exc=exc)
            raise ValidationError("Invalid request") from None
        version = request.POST.get("platform_sso_version")
        grant_type = request.POST.get("grant_type")
        handler_func = (
            f"handle_v{version}_{grant_type}".replace("-", "_")
            .replace("+", "_")
            .replace(":", "_")
            .replace(".", "_")
        )
        handler = getattr(self, handler_func, None)
        if not handler:
            LOGGER.debug("Handler not found", handler=handler_func)
            return HttpResponse(status=400)
        LOGGER.debug("sending to handler", handler=handler_func)
        return handler()

    def validate_request_token(self, assertion: str) -> dict[str, Any]:
        # Decode without validation to get header
        header = get_unverified_header(assertion)
        LOGGER.debug("token header", header=header)
        expected_kid = header["kid"]

        self.device_connection = (
            AgentDeviceConnection.objects.filter(apple_sign_key_id=expected_kid)
            .select_related("device")
            .first()
        )
        self.connector = AgentConnector.objects.get(pk=self.device_connection.connector.pk)
        LOGGER.debug("got device", device=self.device_connection.device)

        expected_aud = self.request.build_absolute_uri(
            reverse("authentik_enterprise_endpoints_connectors_agent:psso-token")
        )
        if not self.device_connection.apple_signing_key:
            LOGGER.warning("Failed to issue token for device, no apple_signing_key")
            raise ValidationError("Invalid request")
        # Properly decode the JWT with the key from the device
        decoded = decode(
            assertion,
            self.device_connection.apple_signing_key,
            algorithms=["ES256"],
            audience=expected_aud,
            issuer=str(self.connector.pk),
        )
        self.remote_nonce = decoded.get("nonce")

        # Check that the nonce hasn't been used before
        nonce = AppleNonce.filter_not_expired(nonce=decoded["request_nonce"]).first()
        if not nonce:
            raise ValidationError("Invalid nonce")
        self.nonce = nonce
        nonce.delete()
        return decoded

    def validate_embedded_assertion(self, assertion: str) -> tuple[AgentDeviceUserBinding, dict]:
        """Decode an embedded assertion and validate it by looking up the matching device user"""
        decode_unvalidated = get_unverified_header(assertion)
        expected_kid = decode_unvalidated["kid"]

        device_user = AgentDeviceUserBinding.objects.filter(
            target=self.device_connection.device, apple_enclave_key_id=expected_kid
        ).first()
        if not device_user:
            LOGGER.warning("Could not find device user binding for user")
            raise ValidationError("Invalid request")
        decoded: dict[str, Any] = decode(
            assertion,
            device_user.apple_secure_enclave_key,
            audience=str(self.device_connection.device.pk),
            algorithms=["ES256"],
        )
        if decoded.get("nonce") != self.jwt_request.get("nonce"):
            LOGGER.warning("Mis-matched nonce to outer assertion")
            raise ValidationError("Invalid nonce")
        return device_user, decoded

    def create_auth_session(self, user: User):
        event = Event.new(EventAction.LOGIN).from_http(self.request, user=user)
        store = SessionStore()
        store[SESSION_LOGIN_EVENT] = event
        store.save()
        session = Session.objects.filter(session_key=store.session_key).first()
        session.expires = self.now + timedelta_from_string(self.connector.auth_session_duration)
        AuthenticatedSession.objects.create(session=session, user=user)
        session = SessionMiddleware.encode_session(store.session_key, user)
        return session

    def create_id_token(self, user: User, **kwargs):
        issuer = self.request.build_absolute_uri(
            reverse("authentik_enterprise_endpoints_connectors_agent:psso-token")
        )
        id_token = IDToken(
            iss=issuer,
            sub=user.username,
            aud=str(self.connector.pk),
            exp=int(
                (self.now + timedelta_from_string(self.connector.auth_session_duration)).timestamp()
            ),
            iat=int(now().timestamp()),
            **kwargs,
        )
        kp = CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first()
        return encode(
            id_token.to_dict(),
            kp.private_key,
            headers={
                "kid": kp.kid,
            },
            algorithm=JWTAlgorithms.from_private_key(kp.private_key),
        )

    def handle_v1_0_urn_ietf_params_oauth_grant_type_jwt_bearer(self):
        try:
            user, inner = self.validate_embedded_assertion(self.jwt_request["assertion"])
        except PyJWTError as exc:
            LOGGER.warning("failed to validate inner assertion", exc=exc)
            raise ValidationError("Invalid request") from None
        id_token = self.create_id_token(user.user)
        auth_token = DeviceAuthenticationToken.objects.create(
            device=self.device_connection.device,
            connector=self.connector,
            user=user.user,
            device_token=self.nonce.device_token,
        )
        return JWEResponse(
            {
                "refresh_token": auth_token.token,
                "refresh_token_expires_in": int((auth_token.expires - now()).total_seconds()),
                "id_token": id_token,
                "token_type": TOKEN_TYPE,
                "session_key": self.create_auth_session(user.user),
            },
            device=self.device_connection,
            apv=self.jwt_request["jwe_crypto"]["apv"],
        )
