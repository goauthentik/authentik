from base64 import b64encode, urlsafe_b64decode, urlsafe_b64encode
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
from django.http import HttpRequest, HttpResponse, JsonResponse
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
from authentik.endpoints.connectors.agent.auth import agent_auth_issue_token
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    AgentDeviceUserBinding,
    AppleAuthorizationCode,
    AppleIndependentSecureEnclave,
    AppleNonce,
    AppleUnlockKey,
    DeviceAuthenticationToken,
)
from authentik.enterprise.endpoints.connectors.agent.http import JWEResponse
from authentik.events.models import Event, EventAction
from authentik.events.signals import SESSION_LOGIN_EVENT
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow
from authentik.flows.planner import (
    PLAN_CONTEXT_DEVICE,
    PLAN_CONTEXT_PENDING_USER,
    FlowPlanner,
)
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import JWTAlgorithms
from authentik.root.middleware import SessionMiddleware
from authentik.stages.password.models import PasswordStage
from authentik.stages.password.stage import authenticate

LOGGER = get_logger()
# Seeded by blueprints/default/flow-endpoints-agent-psso-password.yaml
PSSO_PASSWORD_FLOW_SLUG = "endpoints-agent-psso-password"
LOGIN_REQUEST_TYPE = "platformsso-login-request+jwt"
KEY_REQUEST_TYPE = "platformsso-key-request+jwt"


class InvalidCredentials(Exception):
    """The credential in a Platform SSO login request was wrong.

    Kept distinct from ValidationError because macOS has to tell the two apart. Apple's
    ASAuthorizationProviderExtensionLoginConfiguration treats an HTTP 401 as a bad
    credential and anything else as a general failure unless the extension supplies an
    invalidCredentialPredicate to parse the body; only the former re-prompts the user for
    their password instead of failing the login outright."""


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(View):
    device_connection: AgentDeviceConnection
    connector: AgentConnector

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # This is a plain Django View, so DRF's exception handler never runs and a
        # ValidationError raised below would surface as a 500 instead of a 400.
        try:
            return super().dispatch(request, *args, **kwargs)
        except InvalidCredentials:
            # 401 with a JSON body, which is what macOS reads as "wrong password" without
            # the extension needing an invalidCredentialPredicate. The body deliberately
            # says no more than that: this endpoint is unauthenticated.
            return JsonResponse({"error": "invalid_grant"}, status=401)
        except ValidationError as exc:
            LOGGER.warning("Invalid Platform SSO token request", exc=exc)
            return HttpResponse(status=400)

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
        if self.jwt_request is None:
            return HttpResponse(status=400)
        version = request.POST.get("platform_sso_version")
        # The form's grant_type describes the transport: macOS posts every Platform SSO
        # login as jwt-bearer, including password logins. The grant_type that actually
        # describes the request is a claim of the signed login request, so prefer it and
        # fall back to the form for requests that don't carry one.
        grant_type = self.jwt_request.get("grant_type") or request.POST.get("grant_type")
        handler_func = (
            f"handle_v{version}_{grant_type}".replace("-", "_")
            .replace("+", "_")
            .replace(":", "_")
            .replace(".", "_")
        )
        handler = getattr(self, handler_func, None)
        if not handler:
            # Log the claim names (never the values) so an unsupported grant can be
            # identified from the logs without reproducing under a debugger.
            LOGGER.warning(
                "No handler for Platform SSO grant",
                handler=handler_func,
                version=version,
                grant_type=grant_type,
                request_claims=sorted(self.jwt_request.keys()),
            )
            return HttpResponse(status=400)
        LOGGER.debug(
            "sending to handler",
            handler=handler_func,
            request_claims=sorted(self.jwt_request.keys()),
            # The form's grant_type is not always the one that describes the request: the
            # login request JWT carries its own. Log both (never a credential value) so the
            # two can be told apart.
            request_grant_type=self.jwt_request.get("grant_type"),
            request_amr=self.jwt_request.get("amr"),
        )
        return handler()

    def log_unhandled_request_type(self, assertion: str, header: dict[str, Any]) -> None:
        """Describe a Platform SSO request this endpoint does not implement.

        macOS posts more than login and key requests here, and an unimplemented type would
        otherwise leave nothing behind but a 400. Records the claim names only."""
        typ = header.get("typ")
        if typ in (LOGIN_REQUEST_TYPE, KEY_REQUEST_TYPE):
            return
        try:
            decoded = decode(
                assertion,
                self.device_connection.apple_signing_key,
                algorithms=["ES256"],
                issuer=str(self.connector.pk),
                options={"verify_aud": False, "verify_exp": False},
            )
        except PyJWTError as exc:
            LOGGER.warning("Unhandled Platform SSO request type, undecodable", typ=typ, exc=exc)
            return
        LOGGER.warning(
            "Unhandled Platform SSO request type",
            typ=typ,
            request_claims=sorted(decoded.keys()),
        )

    def validate_request_token(self, assertion: str) -> dict[str, Any] | None:
        # Decode without validation to get header
        header = get_unverified_header(assertion)
        LOGGER.debug("token header", header=header)
        expected_kid = header.get("kid")
        if not expected_kid:
            LOGGER.warning("Request token carries no key ID", header=header)
            return None

        self.device_connection = (
            AgentDeviceConnection.objects.filter(apple_sign_key_id=expected_kid)
            .select_related("device")
            .first()
        )
        if not self.device_connection:
            LOGGER.warning("No device connection found for key ID", kid=expected_kid)
            return None
        self.connector = AgentConnector.objects.get(pk=self.device_connection.connector.pk)
        if not self.device_connection.apple_signing_key:
            LOGGER.warning("Failed to issue token for device, no apple_signing_key")
            raise ValidationError("Invalid request")
        self.log_unhandled_request_type(assertion, header)
        # Key requests carry no aud claim. Apple's own table marks it required, but neither
        # the client nor the sample messages `app-sso platform -m` prints include one, so
        # requiring it here would reject every key request. The signature, issuer, nonce and
        # expiry checks below still apply.
        audience_options = (
            {"options": {"verify_aud": False}}
            if header.get("typ") == KEY_REQUEST_TYPE
            else {
                "audience": self.request.build_absolute_uri(
                    reverse("authentik_enterprise_endpoints_connectors_agent:psso-token")
                )
            }
        )
        # Properly decode the JWT with the key from the device
        decoded = decode(
            assertion,
            self.device_connection.apple_signing_key,
            algorithms=["ES256"],
            issuer=str(self.connector.pk),
            **audience_options,
        )
        self.remote_nonce = decoded.get("nonce")

        # Check that the nonce hasn't been used before
        request_nonce = decoded.get("request_nonce")
        if not request_nonce:
            LOGGER.warning("Request token carries no request_nonce", claims=sorted(decoded.keys()))
            raise ValidationError("Invalid request")
        nonce = AppleNonce.objects.filter(nonce=request_nonce).first()
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

    @staticmethod
    def ecdh_shared_key(cert_private_key_pem: str, other_publickey_b64: str) -> bytes:
        """ECDH between our unlock key and the device's ephemeral public key. The device
        regenerates its side per-request, so `other_publickey` must come from the request
        being handled, never from registration or a previous request."""
        private_key = serialization.load_pem_private_key(
            cert_private_key_pem.encode(), password=None
        )
        other_pubkey_bytes = urlsafe_b64decode(
            other_publickey_b64 + "=" * (-len(other_publickey_b64) % 4)
        )
        other_public_key = EllipticCurvePublicKey.from_encoded_point(
            SECP256R1(), other_pubkey_bytes
        )
        return private_key.exchange(ECDH(), other_public_key)

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
        claims = kwargs.pop("claims", {})
        # Only http(s) avatars are usable by the client, the initials fallback is an
        # inline SVG data URI which macOS can't decode
        avatar = user.avatar
        if avatar.startswith(("http://", "https://")):
            claims["picture"] = avatar
        issuer = self.request.build_absolute_uri(
            reverse("authentik_enterprise_endpoints_connectors_agent:psso-token")
        )
        id_token = IDToken(
            iss=issuer,
            sub=str(user.uuid),
            aud=str(self.connector.pk),
            exp=int(
                (self.now + timedelta_from_string(self.connector.auth_session_duration)).timestamp()
            ),
            iat=int(now().timestamp()),
            claims=claims,
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

    def issue_refresh_token(self, user: User) -> DeviceAuthenticationToken:
        """Mint the refresh token a login response hands back.

        The token has to be signed and stored, not just recorded as a row: macOS keeps it
        and presents it on every key request and refresh, and Platform SSO 2.0 treats it as
        the authorisation for both. Creating the row without a token yields an empty
        refresh_token, which the client dutifully echoes back and nothing can verify."""
        auth_token = DeviceAuthenticationToken.objects.create(
            device=self.device_connection.device,
            connector=self.connector,
            user=user,
            device_token=self.nonce.device_token,
        )
        token, expires = agent_auth_issue_token(
            self.device_connection.device,
            self.connector,
            user,
            jti=str(auth_token.identifier),
        )
        if not token or not expires:
            LOGGER.warning("Failed to issue Platform SSO refresh token")
            raise ValidationError("Invalid request")
        auth_token.token = token
        auth_token.expires = expires
        auth_token.expiring = True
        auth_token.save()
        return auth_token

    def login_response(self, user: User) -> JWEResponse:
        """Build the shared login response for the jwt-bearer, password and authorization_code
        grants, optionally including the ECDH key material for lock-screen unlock."""
        auth_token = self.issue_refresh_token(user)
        body = {
            "refresh_token": auth_token.token,
            "refresh_token_expires_in": int((auth_token.expires - self.now).total_seconds()),
            "id_token": self.create_id_token(user),
            "token_type": TOKEN_TYPE,
            "session_key": self.create_auth_session(user),
        }
        if "urn:apple:platformsso:auth:unlock" in self.jwt_request.get("scope", ""):
            unlock_key = (
                AppleUnlockKey.objects.filter(
                    device_user__user=user,
                    device_user__target=self.device_connection.device,
                )
                .order_by("-expires")
                .first()
            )
            other_publickey = self.jwt_request.get("other_publickey")
            if not unlock_key or not other_publickey:
                LOGGER.warning(
                    "auth:unlock requested without a provisioned key or public key", user=user
                )
            else:
                body["key"] = b64encode(
                    self.ecdh_shared_key(unlock_key.private_key, other_publickey)
                ).decode()
                body["key_context"] = str(unlock_key.identifier)
                LOGGER.debug("Attached unlock key", key_context=unlock_key.identifier)
        return JWEResponse(
            body,
            device=self.device_connection,
            apv=self.jwt_request["jwe_crypto"]["apv"],
        )

    def handle_v1_0_password(self) -> HttpResponse:
        """Apple Platform SSO password login.

        macOS collects the credential at the login window and sends it as claims of the
        signed login request, so nothing interactive is left to do. The dedicated flow is
        planned to apply its policies, then its password stage's configured backends do
        the authentication -- reusing the stage's backend list rather than hardcoding one
        keeps LDAP- and Kerberos-sourced users working here as they do in a browser."""
        username = self.jwt_request.get("username")
        password = self.jwt_request.get("password")
        if not username or not password:
            LOGGER.warning(
                "Password login request missing credentials",
                request_claims=sorted(self.jwt_request.keys()),
            )
            raise ValidationError("Invalid request")
        flow = Flow.objects.filter(slug=PSSO_PASSWORD_FLOW_SLUG).first()
        stage = PasswordStage.objects.filter(flow__slug=PSSO_PASSWORD_FLOW_SLUG).first()
        if not flow or not stage:
            LOGGER.warning(
                "Platform SSO password flow is missing or has no password stage",
                slug=PSSO_PASSWORD_FLOW_SLUG,
            )
            raise ValidationError("Invalid request")
        user = User.objects.filter(username=username).first()
        if not user:
            # Deliberately the same response as a bad password: the token endpoint is
            # unauthenticated, so distinguishing the two would enumerate usernames.
            LOGGER.info("Platform SSO password login for unknown user")
            raise InvalidCredentials
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        try:
            planner.plan(self.request, {PLAN_CONTEXT_PENDING_USER: user})
        except FlowNonApplicableException:
            LOGGER.info("Platform SSO password login denied by flow policies")
            raise ValidationError("Invalid request") from None
        authenticated = authenticate(
            self.request, stage.backends, stage, username=username, password=password
        )
        if not authenticated:
            LOGGER.info("Platform SSO password login failed")
            raise InvalidCredentials
        return self.login_response(authenticated)

    def handle_v1_0_urn_ietf_params_oauth_grant_type_token_exchange(self) -> HttpResponse:
        # Dispatched on the grant_type claim of the login request, see post()
        device_user = AgentDeviceUserBinding.objects.filter(
            target=self.device_connection.device, user__username=self.jwt_request["sub"]
        ).first()
        if not device_user:
            LOGGER.warning("No device user binding for token exchange")
            raise ValidationError("Invalid request")
        return self.login_response(device_user.user)

    def handle_v1_0_urn_ietf_params_oauth_grant_type_jwt_bearer(self) -> HttpResponse:
        embedded = self.jwt_request.get("assertion")
        if not embedded:
            # A jwt-bearer login request carries the inner assertion signed by the user's
            # Secure Enclave key. macOS omits it when that key is not usable for the
            # request, and without it there is nothing to authenticate against.
            LOGGER.warning(
                "Login request carries no embedded assertion",
                request_claims=sorted(self.jwt_request.keys()),
            )
            raise ValidationError("Invalid request")
        try:
            device_user, _ = self.validate_embedded_assertion(embedded)
        except PyJWTError as exc:
            LOGGER.warning("failed to validate inner assertion", exc=exc)
            raise ValidationError("Invalid request") from exc
        return self.login_response(device_user.user)

    def handle_v1_0_authorization_code(self) -> HttpResponse:
        code = self.request.POST.get("code")
        if not code:
            return HttpResponse(status=400)
        auth_code = AppleAuthorizationCode.objects.filter(
            code=code,
            connector=self.connector,
        ).first()
        if not auth_code:
            LOGGER.warning("Authorization code not found")
            return HttpResponse(status=400)
        # Without this, any other device enrolled in the same connector could redeem the code
        if auth_code.device_connection_id != self.device_connection.pk:
            LOGGER.warning("Authorization code redeemed by a different device")
            return HttpResponse(status=400)
        user = auth_code.user
        auth_code.delete()
        return self.login_response(user)

    def handle_v2_0_urn_ietf_params_oauth_grant_type_jwt_bearer(self) -> HttpResponse:
        request_type = self.jwt_request.get("request_type")
        LOGGER.debug("v2.0 request", request_type=request_type)
        if request_type == "key_request":
            return self.handle_key_request()
        if request_type == "key_exchange":
            return self.handle_key_exchange()
        LOGGER.debug("Unknown request_type for v2.0", request_type=request_type)
        return HttpResponse(status=400)

    def validate_refresh_token(self) -> DeviceAuthenticationToken:
        auth_token = (
            DeviceAuthenticationToken.objects.filter(
                token=self.jwt_request.get("refresh_token"),
                device=self.device_connection.device,
            )
            .select_related("user")
            .first()
        )
        if not auth_token:
            raise ValidationError("Invalid refresh token")
        return auth_token

    def handle_key_request(self) -> HttpResponse:
        auth_token = self.validate_refresh_token()
        device_user = AgentDeviceUserBinding.objects.filter(
            target=self.device_connection.device,
            user=auth_token.user,
        ).first()
        if not device_user:
            LOGGER.warning("No device user binding found for key request")
            return HttpResponse(status=400)

        expires_at = self.now + timedelta_from_string(self.connector.auth_session_duration)
        # Return the same certificate bytes for as long as the key is valid, so macOS sees an
        # identical tokenID (SHA-1 of the public key) and doesn't attempt to rotate the key,
        # which would require com.apple.PlatformSSO.login.service-xpc.
        unlock_key = (
            AppleUnlockKey.objects.filter(device_user=device_user)
            .exclude(certificate_der="")
            .first()
        )
        if unlock_key:
            LOGGER.debug("Reusing unlock key", key_context=unlock_key.identifier)
        else:
            private_key = generate_private_key(SECP256R1())
            subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, auth_token.user.username)])
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(subject)
                .public_key(private_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(self.now)
                .not_valid_after(expires_at)
                .add_extension(
                    x509.KeyUsage(
                        digital_signature=True,
                        key_agreement=True,
                        key_cert_sign=False,
                        content_commitment=False,
                        key_encipherment=False,
                        data_encipherment=False,
                        crl_sign=False,
                        encipher_only=False,
                        decipher_only=False,
                    ),
                    critical=True,
                )
                .add_extension(
                    x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
                    critical=False,
                )
                .sign(private_key, hashes.SHA256())
            )
            unlock_key = AppleUnlockKey.objects.create(
                device_user=device_user,
                private_key=private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                ).decode(),
                certificate_der=urlsafe_b64encode(cert.public_bytes(serialization.Encoding.DER))
                .rstrip(b"=")
                .decode(),
                expires=expires_at,
            )
            LOGGER.debug("Created unlock key", key_context=unlock_key.identifier)
        return JWEResponse(
            {
                "certificate": unlock_key.certificate_der,
                "exp": int(expires_at.timestamp()),
                "iat": int(self.now.timestamp()),
                "key_context": str(unlock_key.identifier),
            },
            device=self.device_connection,
            apv=self.jwt_request["jwe_crypto"]["apv"],
            typ="platformsso-key-response+jwt",
        )

    def handle_key_exchange(self) -> HttpResponse:
        auth_token = self.validate_refresh_token()
        try:
            key_context = UUID(self.jwt_request.get("key_context", ""))
        except ValueError:
            LOGGER.warning("Missing or invalid key_context in key exchange request")
            return HttpResponse(status=400)
        unlock_key = AppleUnlockKey.objects.filter(
            identifier=key_context,
            device_user__user=auth_token.user,
            device_user__target=self.device_connection.device,
        ).first()
        if not unlock_key:
            LOGGER.warning("No unlock key found for key_context", key_context=key_context)
            return HttpResponse(status=400)

        expires_at = self.now + timedelta_from_string(self.connector.auth_session_duration)
        return JWEResponse(
            {
                "key": b64encode(
                    self.ecdh_shared_key(
                        unlock_key.private_key, self.jwt_request["other_publickey"]
                    )
                ).decode(),
                "exp": int(expires_at.timestamp()),
                "iat": int(self.now.timestamp()),
                "key_context": str(unlock_key.identifier),
            },
            device=self.device_connection,
            apv=self.jwt_request["jwe_crypto"]["apv"],
            typ="platformsso-key-response+jwt",
        )
