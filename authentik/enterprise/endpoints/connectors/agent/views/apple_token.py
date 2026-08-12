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


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(View):

    device_connection: AgentDeviceConnection
    connector: AgentConnector

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # This is a plain Django View, so DRF's exception handler never runs and a
        # ValidationError raised below would surface as a 500 instead of a 400.
        try:
            return super().dispatch(request, *args, **kwargs)
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
            raise ValidationError("Invalid request")
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
            raise ValidationError("Invalid request")
        id_token = self.create_id_token(authenticated)
        auth_token = DeviceAuthenticationToken.objects.create(
            device=self.device_connection.device,
            connector=self.connector,
            user=authenticated,
            device_token=self.nonce.device_token,
        )
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
