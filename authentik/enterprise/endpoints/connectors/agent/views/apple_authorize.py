from datetime import timedelta
from uuid import UUID

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.utils.http import urlencode
from django.utils.timezone import now
from django.views import View
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.endpoints.connectors.agent.auth import check_device_policies
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AppleAuthorizationCode,
)
from authentik.endpoints.models import Device
from authentik.enterprise.policy import EnterprisePolicyAccessView
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import FlowPlanner
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER, StageView

LOGGER = get_logger()

PLAN_CONTEXT_PSSO_STATE = "psso_state"
PLAN_CONTEXT_PSSO_REDIRECT_URI = "psso_redirect_uri"
PLAN_CONTEXT_PSSO_CONNECTOR = "psso_connector"
PLAN_CONTEXT_PSSO_SCOPE = "psso_scope"

_ALLOWED_REDIRECT_URIS = {"com.apple.PlatformSSO://callback"}

connector_id = "759c519c-92f5-4f7e-8547-10b44274a157"
device_id = "1e5baefa-e6fd-4074-a06b-69b9107ae537"

class PSSORedirect(HttpResponseRedirect):
    allowed_schemes = ["com.apple.platformsso", "com.apple.PlatformSSO"]


class AppleAuthorizeView(EnterprisePolicyAccessView):

    connector: AgentConnector

    def resolve_provider_application(self):
        self.device = Device.objects.filter(pk=device_id).first()
        self.connector = AgentConnector.objects.filter(pk=connector_id).first()

    def user_has_access(self, user=None, pbm=None):
        enterprise_result = self.check_license()
        if not enterprise_result.passing:
            return enterprise_result
        return check_device_policies(self.device, user or self.request.user, self.request)

    def modify_flow_context(self, flow, context):
        if QS_LOGIN_HINT in self.request.GET:
            context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = self.request.GET[QS_LOGIN_HINT]
        return super().modify_flow_context(flow, context)

    def get(self, request: HttpRequest) -> HttpResponse:
        redirect_uri = request.GET.get("redirect_uri", "")
        if redirect_uri not in _ALLOWED_REDIRECT_URIS:
            return HttpResponseBadRequest("Invalid redirect_uri")

        if not self.connector.authorization_flow:
            return HttpResponseBadRequest("No authorization flow configured")

        state = request.GET.get("state", "")
        login_hint = request.GET.get("login_hint")

        planner = FlowPlanner(self.connector.authorization_flow)
        planner.allow_empty_flows = True
        context: dict = {
            PLAN_CONTEXT_PSSO_STATE: state,
            PLAN_CONTEXT_PSSO_REDIRECT_URI: redirect_uri,
            PLAN_CONTEXT_PSSO_CONNECTOR: self.connector,
            PLAN_CONTEXT_PSSO_SCOPE: request.GET.get("scope"),
        }
        if login_hint:
            context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = login_hint
        try:
            plan = planner.plan(request, context)
        except FlowNonApplicableException:
            return HttpResponseBadRequest("Flow not applicable")

        plan.append_stage(in_memory_stage(PSSOAuthFulfillmentStage))
        return plan.to_redirect(
            request,
            self.connector.authorization_flow,
            # allowed_silent_types=[PSSOAuthFulfillmentStage],
        )


class PSSOAuthFulfillmentStage(StageView):
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        state: str = self.executor.plan.context.pop(PLAN_CONTEXT_PSSO_STATE, "")
        redirect_uri: str = self.executor.plan.context.pop(PLAN_CONTEXT_PSSO_REDIRECT_URI)
        connector: AgentConnector = self.executor.plan.context.pop(PLAN_CONTEXT_PSSO_CONNECTOR)

        auth_code = AppleAuthorizationCode.objects.create(
            user=request.user,
            connector=connector,
            state=state,
            expires=now() + timedelta(minutes=5),
            scope=self.executor.plan.context.get(PLAN_CONTEXT_PSSO_SCOPE),
        )

        params: dict = {"code": auth_code.code}
        if state:
            params["state"] = state
        return PSSORedirect(redirect_uri + "?" + urlencode(params))
