from django.http import HttpRequest
from django.utils.timezone import now
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from jwt import PyJWTError, decode, encode
from rest_framework.authentication import BaseAuthentication
from structlog.stdlib import get_logger

from authentik.api.authentication import get_authorization_header, validate_auth
from authentik.core.models import User
from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import AgentConnector
from authentik.endpoints.models import Device
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.engine import PolicyEngine
from authentik.policies.models import PolicyBindingModel
from authentik.providers.oauth2.models import AccessToken, JWTAlgorithms, OAuth2Provider

LOGGER = get_logger()
PLATFORM_ISSUER = "goauthentik.io/platform"


def agent_auth_issue_token(device: Device, connector: AgentConnector, user: User, **kwargs):
    kp = CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first()
    if not kp:
        return None, None
    exp = now() + timedelta_from_string(connector.auth_session_duration)
    token = encode(
        {
            "iss": PLATFORM_ISSUER,
            "aud": str(device.pk),
            "iat": int(now().timestamp()),
            "exp": int(exp.timestamp()),
            "preferred_username": user.username,
            **kwargs,
        },
        kp.private_key,
        headers={
            "kid": kp.kid,
        },
        algorithm=JWTAlgorithms.from_private_key(kp.private_key),
    )
    return token, exp


class DeviceAuthFedAuthentication(BaseAuthentication):

    def authenticate(self, request):
        raw_token = validate_auth(get_authorization_header(request))
        if not raw_token:
            LOGGER.warning("Missing token")
            return None
        device = Device.filter_not_expired(name=request.query_params.get("device")).first()
        if not device:
            LOGGER.warning("Couldn't find device")
            return None
        connectors_for_device = AgentConnector.objects.filter(device__in=[device])
        connector = connectors_for_device.first()
        providers = OAuth2Provider.objects.filter(agentconnector__in=connectors_for_device)
        federated_token = AccessToken.objects.filter(
            token=raw_token, provider__in=providers
        ).first()
        if not federated_token:
            LOGGER.warning("Couldn't lookup provider")
            return None
        _key, _alg = federated_token.provider.jwt_key
        try:
            decode(
                raw_token,
                _key.public_key(),
                algorithms=[_alg],
                options={
                    "verify_aud": False,
                },
            )
            LOGGER.info(
                "successfully verified JWT with provider", provider=federated_token.provider.name
            )
            return (federated_token.user, (federated_token, device, connector))
        except (PyJWTError, ValueError, TypeError, AttributeError) as exc:
            LOGGER.warning("failed to verify JWT", exc=exc, provider=federated_token.provider.name)
            return None


class DeviceFederationAuthSchema(OpenApiAuthenticationExtension):
    """Auth schema"""

    target_class = DeviceAuthFedAuthentication
    name = "device_federation"

    def get_security_definition(self, auto_schema):
        """Auth schema"""
        return {"type": "http", "scheme": "bearer"}


def check_device_policies(device: Device, user: User, request: HttpRequest):
    """Check policies bound to device group and device"""
    if device.access_group:
        result = check_pbm_policies(device.access_group, user, request)
        if result.passing:
            return result
    return check_pbm_policies(device, user, request)


def check_pbm_policies(pbm: PolicyBindingModel, user: User, request: HttpRequest):
    policy_engine = PolicyEngine(pbm, user, request)
    policy_engine.use_cache = False
    policy_engine.empty_result = False
    policy_engine.mode = pbm.policy_engine_mode
    policy_engine.build()
    result = policy_engine.result
    LOGGER.debug("PolicyAccessView user_has_access", user=user.username, result=result, pbm=pbm.pk)
    return result
