from base64 import b64decode, b64encode
from datetime import timedelta
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    load_pem_private_key,
)
from cryptography.x509 import load_pem_x509_certificate
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
    AppleIndependentSecureEnclave,
    AppleNonce,
    AppleUserKey,
    DeviceAuthenticationToken,
)
from authentik.enterprise.endpoints.connectors.agent.http import KEY_RESPONSE_TYPE, JWEResponse
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
            raise ValidationError("Invalid request") from None
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
        LOGGER.debug("got device", device=self.device_connection.device)

        expected_aud = self.request.build_absolute_uri(
            reverse("authentik_enterprise_endpoints_connectors_agent:psso-token")
        )
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
            else {"audience": expected_aud}
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

    def authenticated_key_request_user(self) -> User:
        """Resolve and authorise the user behind a key request.

        A key request proves possession of the device signing key and of a refresh token
        issued to that device, which is what authorises minting or using an unlock key. The
        refresh token is checked against the device rather than trusted from the claim, so a
        token issued for one device cannot provision a key on another."""
        refresh_token = self.jwt_request.get("refresh_token")
        if not refresh_token:
            LOGGER.warning("Key request carries no refresh token")
            raise ValidationError("Invalid request")
        auth_token = DeviceAuthenticationToken.objects.filter(
            token=refresh_token,
            device=self.device_connection.device,
            connector=self.connector,
        ).first()
        if not auth_token or not auth_token.user:
            LOGGER.warning("Key request refresh token is not valid for this device")
            raise ValidationError("Invalid request")
        if auth_token.is_expired:
            LOGGER.warning("Key request refresh token has expired")
            raise ValidationError("Invalid request")
        return auth_token.user

    def key_request_username(self) -> str:
        username = self.jwt_request.get("username") or self.jwt_request.get("sub")
        if not username:
            LOGGER.warning(
                "Key request carries no username", request_claims=sorted(self.jwt_request.keys())
            )
            raise ValidationError("Invalid request")
        return username

    def key_response(self, body: dict) -> JWEResponse:
        now_ts = int(self.now.timestamp())
        return JWEResponse(
            {
                # Apple specifies a five minute window for both key responses.
                "exp": now_ts + 300,
                "iat": now_ts,
                **body,
            },
            device=self.device_connection,
            apv=self.jwt_request["jwe_crypto"]["apv"],
            response_type=KEY_RESPONSE_TYPE,
        )

    def handle_v2_0_urn_ietf_params_oauth_grant_type_jwt_bearer(self):
        """Platform SSO 2.0 key service.

        Both the key request and the key exchange arrive as this grant with the same JWT
        type, and are told apart by their request_type claim."""
        request_type = self.jwt_request.get("request_type")
        if request_type == "key_request":
            return self.handle_key_request()
        if request_type == "key_exchange":
            return self.handle_key_exchange()
        LOGGER.warning(
            "Unsupported Platform SSO key request type",
            request_type=request_type,
            request_claims=sorted(self.jwt_request.keys()),
        )
        raise ValidationError("Invalid request")

    def build_key_certificate(self, key_purpose: str, username: str) -> tuple[str, str]:
        """Mint the EC P-256 key and the certificate that carries its public half.

        macOS stores this certificate in the user's keychain for a year and backs a
        CryptoTokenKit identity with it, so it is built as a well-formed end-entity
        certificate: BasicConstraints and SubjectKeyIdentifier make it structurally
        complete, and keyAgreement is the usage the Diffie-Hellman exchange actually
        performs. macOS accepts the extension-less certificate CertificateBuilder
        emits too, but that helper also stamps the running authentik version into the
        issuer name, which has no business in a certificate stored on every enrolled
        device."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name(
            [
                x509.NameAttribute(
                    NameOID.COMMON_NAME, f"Platform SSO {key_purpose} {username}"[:64]
                ),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "authentik"),
            ]
        )
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(self.now - timedelta(days=1))
            .not_valid_after(self.now + timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=False,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=True,
                    key_cert_sign=False,
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
        return (
            private_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=NoEncryption(),
            ).decode(),
            certificate.public_bytes(Encoding.PEM).decode(),
        )

    def handle_key_request(self):
        """Provision the key macOS binds to the user's account.

        Apple requires the public half to come back inside a certificate so that keychain
        operations can find it. The key is minted once per device, login name and purpose:
        re-provisioning on a repeat request would invalidate the key bag the previous one
        unlocked."""
        user = self.authenticated_key_request_user()
        username = self.key_request_username()
        key_purpose = self.jwt_request.get("key_purpose", "user_unlock")
        key = AppleUserKey.objects.filter(
            device_connection=self.device_connection,
            username=username,
            key_purpose=key_purpose,
        ).first()
        if not key:
            private_key, certificate = self.build_key_certificate(key_purpose, username)
            key = AppleUserKey.objects.create(
                device_connection=self.device_connection,
                username=username,
                key_purpose=key_purpose,
                certificate=certificate,
                private_key=private_key,
            )
            LOGGER.info(
                "Provisioned Platform SSO key",
                user=user,
                username=username,
                key_purpose=key_purpose,
            )
        certificate = load_pem_x509_certificate(key.certificate.encode())
        return self.key_response(
            {
                "certificate": b64encode(certificate.public_bytes(Encoding.DER)).decode(),
                "key_context": key.key_context,
            }
        )

    def handle_key_exchange(self):
        """Complete a Diffie-Hellman exchange against the provisioned key.

        macOS sends its own public key and expects the raw shared secret back, which it uses
        to unlock the user's key bag. This runs while the user waits at the login window, so
        it does no more work than the exchange itself."""
        self.authenticated_key_request_user()
        username = self.key_request_username()
        key_purpose = self.jwt_request.get("key_purpose", "user_unlock")
        key = AppleUserKey.objects.filter(
            device_connection=self.device_connection,
            username=username,
            key_purpose=key_purpose,
        ).first()
        if not key:
            LOGGER.warning(
                "Key exchange for a key that was never provisioned",
                username=username,
                key_purpose=key_purpose,
            )
            raise ValidationError("Invalid request")
        other_publickey = self.jwt_request.get("other_publickey")
        if not other_publickey:
            LOGGER.warning("Key exchange carries no other_publickey")
            raise ValidationError("Invalid request")
        try:
            # The peer key is an ANSI X9.63 point (0x04 || X || Y), the same encoding the
            # device signing and encryption keys use.
            peer_key = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(), b64decode(other_publickey)
            )
            private_key = load_pem_private_key(key.private_key.encode(), password=None)
            shared_secret = private_key.exchange(ec.ECDH(), peer_key)
        except (ValueError, TypeError) as exc:
            LOGGER.warning("Key exchange failed", exc=exc)
            raise ValidationError("Invalid request") from None
        return self.key_response(
            {
                "key": b64encode(shared_secret).decode(),
                "key_context": key.key_context,
            }
        )

    def handle_v1_0_password(self):
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
        id_token = self.create_id_token(authenticated)
        auth_token = self.issue_refresh_token(authenticated)
        return JWEResponse(
            {
                "refresh_token": auth_token.token,
                "refresh_token_expires_in": int((auth_token.expires - now()).total_seconds()),
                "id_token": id_token,
                "token_type": TOKEN_TYPE,
                "session_key": self.create_auth_session(authenticated),
            },
            device=self.device_connection,
            apv=self.jwt_request["jwe_crypto"]["apv"],
        )

    def handle_v1_0_urn_ietf_params_oauth_grant_type_jwt_bearer(self):
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
            user, inner = self.validate_embedded_assertion(embedded)
        except PyJWTError as exc:
            LOGGER.warning("failed to validate inner assertion", exc=exc)
            raise ValidationError("Invalid request") from None
        id_token = self.create_id_token(user.user)
        auth_token = self.issue_refresh_token(user.user)
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
