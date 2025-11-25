from datetime import timedelta
from hashlib import sha256
from hmac import compare_digest

from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest, QueryDict
from django.utils.timezone import now
from jwt import encode

from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import AgentConnector, DeviceAuthenticationToken
from authentik.endpoints.models import Device
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import FlowPlanner
from authentik.flows.stage import StageView
from authentik.policies.views import PolicyAccessView
from authentik.providers.oauth2.models import JWTAlgorithms
from authentik.providers.oauth2.utils import HttpResponseRedirectScheme

PLAN_CONTEXT_DEVICE = "goauthentik.io/endpoints/device"
PLAN_CONTEXT_DEVICE_AUTH_TOKEN = "goauthentik.io/endpoints/device_auth_token"  # nosec

QS_AGENT_IA_TOKEN = "ak-auth-ia-token"  # nosec


class AgentInteractiveAuth(PolicyAccessView):
    """Agent device authentication"""

    auth_token: DeviceAuthenticationToken
    device: Device
    connector: AgentConnector

    def resolve_provider_application(self):
        auth_token = (
            DeviceAuthenticationToken.objects.filter(identifier=self.kwargs["token_uuid"])
            .prefetch_related()
            .first()
        )
        if not auth_token:
            raise Http404
        self.auth_token = auth_token
        self.device = auth_token.device
        self.connector = auth_token.connector.agentconnector

    def user_has_access(self, user=None, pbm=None):
        return super().user_has_access(user, self.device)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        device_token_hash = request.headers.get("X-Authentik-Platform-Auth-DTH")
        if not compare_digest(
            device_token_hash, sha256(self.auth_token.device_token.key.encode()).hexdigest()
        ):
            return HttpResponseBadRequest("Invalid device token")

        planner = FlowPlanner(self.connector.authorization_flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                self.request,
                {
                    PLAN_CONTEXT_DEVICE: self.device,
                    PLAN_CONTEXT_DEVICE_AUTH_TOKEN: self.auth_token,
                },
            )
        except FlowNonApplicableException:
            return self.handle_no_permission_authenticated()
        plan.append_stage(in_memory_stage(AgentAuthFulfillmentStage))

        return plan.to_redirect(
            self.request,
            self.connector.authorization_flow,
            allowed_silent_types=[AgentAuthFulfillmentStage],
        )


class AgentAuthFulfillmentStage(StageView):

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        device: Device = self.executor.plan.context.pop(PLAN_CONTEXT_DEVICE)
        auth_token: DeviceAuthenticationToken = self.executor.plan.context.pop(
            PLAN_CONTEXT_DEVICE_AUTH_TOKEN
        )

        kp = CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first()
        token = encode(
            {
                "iss": "goauthentik.io/platform",
                "aud": str(device.pk),
                "jti": str(auth_token.identifier),
                "iat": int(now().timestamp()),
                "exp": int((now() + timedelta(days=3)).timestamp()),
                "preferred_username": request.user.username,
            },
            kp.private_key,
            algorithm=JWTAlgorithms.from_private_key(kp.private_key),
        )
        qd = QueryDict(mutable=True)
        qd[QS_AGENT_IA_TOKEN] = token
        auth_token.token = token
        auth_token.save()
        return HttpResponseRedirectScheme(
            "goauthentik.io://platform/finished?" + qd.urlencode(),
            allowed_schemes=["goauthentik.io"],
        )
