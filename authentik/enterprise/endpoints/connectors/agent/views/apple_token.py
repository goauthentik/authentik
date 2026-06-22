from base64 import b64decode, urlsafe_b64encode
from datetime import timezone as dt_timezone
from typing import Any
from uuid import UUID

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDH,
    SECP256R1,
    EllipticCurvePublicKey,
    generate_private_key,
)
from cryptography.x509.oid import NameOID
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from jwt import PyJWTError, decode, encode, get_unverified_header
from rest_framework.exceptions import ValidationError
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import TOKEN_TYPE
from authentik.core.models import AuthenticatedSession, Session, User
from authentik.core.sessions import SessionStore
from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    AgentDeviceUserBinding,
    AppleIndependentSecureEnclave,
    AppleNonce,
    AppleUnlockKey,
    DeviceAuthenticationToken,
)
from authentik.enterprise.endpoints.connectors.agent.http import JWEResponse
from authentik.events.models import Event, EventAction
from authentik.events.signals import SESSION_LOGIN_EVENT
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.lib.utils.time import timedelta_from_string
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
            raise ValidationError("Invalid request") from exc
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

        kwargs = {
            "issuer": str(self.connector.pk)
        }
        if header["typ"] == "platformsso-key-request+jwt":
            pass
        elif header["typ"] == "platformsso-login-request+jwt":
            expected_aud = self.request.build_absolute_uri(
                reverse("authentik_enterprise_endpoints_connectors_agent:psso-token")
            )
            if not self.device_connection.apple_signing_key:
                LOGGER.warning("Failed to issue token for device, no apple_signing_key")
                raise ValidationError("Invalid request")
            kwargs["audience"] =expected_aud
        # Properly decode the JWT with the key from the device
        decoded = decode(
            assertion,
            self.device_connection.apple_signing_key,
            algorithms=["ES256"],
            **kwargs
        )
        self.remote_nonce = decoded.get("nonce")

        # Check that the nonce hasn't been used before
        nonce = AppleNonce.objects.filter(nonce=decoded["request_nonce"]).first()
        if not nonce:
            raise ValidationError("Invalid nonce")
        self.nonce = nonce
        nonce.delete()
        return decoded

    def validate_embedded_assertion(
        self, assertion: str
    ) -> tuple[AgentDeviceUserBinding | AppleIndependentSecureEnclave, dict]:
        """Decode an embedded assertion and validate it by looking up the matching device user"""
        decode_unvalidated = get_unverified_header(assertion)
        expected_kid = decode_unvalidated["kid"]

        device_user = AgentDeviceUserBinding.objects.filter(
            target=self.device_connection.device, apple_enclave_key_id=expected_kid
        ).first()
        if not device_user:
            independent_user = AppleIndependentSecureEnclave.objects.filter(
                apple_enclave_key_id=expected_kid
            ).first()
            if not independent_user:
                LOGGER.warning("Could not find device user binding or independent enclave for user")
                raise ValidationError("Invalid request")
            device_user = independent_user
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
        event = Event.new(
            EventAction.LOGIN,
            app="authentik.endpoints.connectors.agent",
            **{
                PLAN_CONTEXT_DEVICE: self.device_connection.device,
            },
        ).from_http(self.request, user=user)
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
        if self.jwt_request.get("grant_type") == "urn:ietf:params:oauth:grant-type:token-exchange":
            user = AgentDeviceUserBinding.objects.filter(
                user__username=self.jwt_request["sub"]
            ).first()
        else:
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

    def handle_v2_0_urn_ietf_params_oauth_grant_type_jwt_bearer(self):
        request_type = self.jwt_request.get("request_type")
        if request_type == "key_request":
            return self._handle_key_request()
        if request_type == "key_exchange":
            return self._handle_key_exchange()
        LOGGER.debug("Unknown request_type for v2.0", request_type=request_type)
        return HttpResponse(status=400)

    def _validate_refresh_token(self) -> DeviceAuthenticationToken:
        token = self.jwt_request.get("refresh_token")
        auth_token = (
            DeviceAuthenticationToken.objects.filter(
                token=token,
                device=self.device_connection.device,
            )
            .select_related("user")
            .first()
        )
        if not auth_token:
            raise ValidationError("Invalid refresh token")
        if auth_token.expires < now():
            auth_token.delete()
            raise ValidationError("Expired refresh token")
        return auth_token

    def _handle_key_request(self) -> HttpResponse:
        auth_token = self._validate_refresh_token()
        device_user = AgentDeviceUserBinding.objects.filter(
            target=self.device_connection.device,
            user=auth_token.user,
        ).first()
        if not device_user:
            LOGGER.warning("No device user binding found for key request")
            return HttpResponse(status=400)

        private_key = generate_private_key(SECP256R1())
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, auth_token.user.username)])
        expires_at = self.now + timedelta_from_string(self.connector.auth_session_duration)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(self.now.astimezone(dt_timezone.utc))
            .not_valid_after(expires_at.astimezone(dt_timezone.utc))
            .sign(private_key, hashes.SHA256())
        )

        unlock_key = AppleUnlockKey.objects.create(
            device_user=device_user,
            private_key=private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode(),
            expires=expires_at,
        )

        cert_b64 = urlsafe_b64encode(cert.public_bytes(serialization.Encoding.DER)).rstrip(b"=").decode()

        return JWEResponse(
            {
                "certificate": cert_b64,
                "exp": int(expires_at.timestamp()),
                "iat": int(self.now.timestamp()),
                "key_context": str(unlock_key.identifier),
            },
            device=self.device_connection,
            apv=self.jwt_request["jwe_crypto"]["apv"],
            typ="platformsso-key-response+jwt",
        )

    def _handle_key_exchange(self) -> HttpResponse:
        auth_token = self._validate_refresh_token()

        raw_context = self.jwt_request.get("key_context")
        if not raw_context:
            LOGGER.warning("Missing key_context in key exchange request")
            return HttpResponse(status=400)
        try:
            key_context_uuid = UUID(raw_context)
        except ValueError:
            LOGGER.warning("Invalid key_context UUID", key_context=raw_context)
            return HttpResponse(status=400)

        unlock_key = AppleUnlockKey.objects.filter(
            identifier=key_context_uuid,
            device_user__user=auth_token.user,
            device_user__target=self.device_connection.device,
        ).first()
        if not unlock_key:
            LOGGER.warning("No unlock key found for key_context", key_context=raw_context)
            return HttpResponse(status=400)

        private_key = serialization.load_pem_private_key(
            unlock_key.private_key.encode(),
            password=None,
        )

        raw_pubkey = self.jwt_request["other_publickey"]
        other_pubkey_bytes = b64decode(raw_pubkey + "=" * (-len(raw_pubkey) % 4))
        other_public_key = EllipticCurvePublicKey.from_encoded_point(SECP256R1(), other_pubkey_bytes)

        shared_key = private_key.exchange(ECDH(), other_public_key)
        expires_at = self.now + timedelta_from_string(self.connector.auth_session_duration)

        return JWEResponse(
            {
                "key": urlsafe_b64encode(shared_key).rstrip(b"=").decode(),
                "exp": int(expires_at.timestamp()),
                "iat": int(self.now.timestamp()),
                "key_context": str(unlock_key.identifier),
            },
            device=self.device_connection,
            apv=self.jwt_request["jwe_crypto"]["apv"],
            typ="platformsso-key-response+jwt",
        )
