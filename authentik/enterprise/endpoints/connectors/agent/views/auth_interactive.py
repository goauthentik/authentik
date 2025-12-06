from hashlib import sha256
from hmac import compare_digest

from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest, QueryDict

from authentik.endpoints.connectors.agent.models import AgentConnector, DeviceAuthenticationToken
from authentik.endpoints.models import Device
from authentik.enterprise.endpoints.connectors.agent.auth import (
    agent_auth_issue_token,
    check_device_policies,
)
from authentik.enterprise.policy import EnterprisePolicyAccessView
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_DEVICE, FlowPlanner
from authentik.flows.stage import StageView
from authentik.providers.oauth2.utils import HttpResponseRedirectScheme

PLAN_CONTEXT_DEVICE_AUTH_TOKEN = "goauthentik.io/endpoints/device_auth_token"  # nosec

QS_AGENT_IA_TOKEN = "ak-auth-ia-token"  # nosec


class AgentInteractiveAuth(EnterprisePolicyAccessView):
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
        enterprise_result = self.check_license()
        if not enterprise_result.passing:
            return enterprise_result
        return check_device_policies(self.device, user or self.request.user, self.request)

    def modify_flow_context(self, flow, context):
        return {
            PLAN_CONTEXT_DEVICE: self.device,
            **context,
        }

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        device_token_hash = request.headers.get("X-Authentik-Platform-Auth-DTH")
        if not device_token_hash:
            return HttpResponseBadRequest("Invalid device token")
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

        token, exp = agent_auth_issue_token(
            device,
            auth_token.connector.agentconnector,
            request.user,
            jti=str(auth_token.identifier),
        )
        if not token or not exp:
            return self.executor.stage_invalid("Failed to generate token")
        auth_token.user = request.user
        auth_token.token = token
        auth_token.expires = exp
        auth_token.expiring = True
        auth_token.save()
        qd = QueryDict(mutable=True)
        qd[QS_AGENT_IA_TOKEN] = token
        return HttpResponseRedirectScheme(
            "goauthentik.io://platform/finished?" + qd.urlencode(),
            allowed_schemes=["goauthentik.io"],
        )
