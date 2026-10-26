from datetime import timedelta

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from jwt import PyJWTError, decode, get_unverified_header
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.endpoints.connectors.agent.auth import check_device_policies
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    AppleAuthorizationCode,
)
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.policy import EnterprisePolicyAccessView
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import FlowPlanner
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER, StageView
from authentik.providers.oauth2.utils import HttpResponseRedirectScheme

LOGGER = get_logger()

PLAN_CONTEXT_PSSO = "goauthentik.io/endpoints/connectors/agent/psso"
REDIRECT_URI = "com.apple.PlatformSSO://callback"


class AppleAuthorizePreauthView(View):
    """Platform SSO federation pre-authentication discovery endpoint, called before Platform
    SSO loads the authorization web view. This is the only point in the flow that isn't a
    plain unauthenticated request, so the `state` Platform SSO validates on the callback is
    generated here and threaded through by AppleAuthorizeView.
    https://developer.apple.com/documentation/authenticationservices/implementing-web-based-authentication
    """

    def get(self, request: HttpRequest, connector_uuid: str) -> HttpResponse:
        if not LicenseKey.get_total().status().is_valid:
            return HttpResponseBadRequest("Enterprise required to access this feature.")
        params = {"state": get_random_string(32), "redirect_uri": REDIRECT_URI}
        if login_hint := request.GET.get("user"):
            params[QS_LOGIN_HINT] = login_hint
        url = request.build_absolute_uri(
            reverse(
                "authentik_enterprise_endpoints_connectors_agent:psso-authorize",
                kwargs={"connector_uuid": connector_uuid},
            )
        )
        return JsonResponse({"authorization_url": f"{url}?{urlencode(params)}"})


@method_decorator(csrf_exempt, name="dispatch")
class AppleAuthorizeView(EnterprisePolicyAccessView):
    """Platform SSO federation authorization endpoint, exchanges a browser-based login for an
    authorization code which the device redeems at the token endpoint."""

    connector: AgentConnector
    device_connection: AgentDeviceConnection

    def resolve_provider_application(self):
        self.connector = get_object_or_404(AgentConnector, pk=self.kwargs["connector_uuid"])
        self.device_connection = self.resolve_device_connection()

    def resolve_device_connection(self) -> AgentDeviceConnection:
        """dynamicOpenID federation POSTs a device-signed JWT ('request' form field) next to the
        same query string a plain GET would carry; it identifies the device the request came
        from. Only dynamicOpenID is supported, plain federation carries no device identity and
        could neither be policy-checked nor bound to the authorization code it receives."""
        assertion = self.request.POST.get("request")
        if not assertion:
            LOGGER.warning("Platform SSO authorization request without a request object")
            raise Http404
        try:
            connection = (
                AgentDeviceConnection.objects.filter(
                    apple_sign_key_id=get_unverified_header(assertion)["kid"],
                    connector=self.connector,
                )
                .select_related("device")
                .first()
            )
            if not connection:
                raise Http404
            decode(
                assertion,
                connection.apple_signing_key,
                algorithms=["ES256"],
                options={"verify_aud": False},
            )
        except (PyJWTError, KeyError) as exc:
            LOGGER.warning("Invalid Platform SSO authorization request JWT", exc=exc)
            raise Http404 from exc
        return connection

    def user_has_access(self, user=None, pbm=None):
        result = self.check_license()
        if not result.passing:
            return result
        return check_device_policies(
            self.device_connection.device, user or self.request.user, self.request
        )

    def modify_flow_context(self, flow, context):
        if QS_LOGIN_HINT in self.request.GET:
            context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = self.request.GET[QS_LOGIN_HINT]
        return super().modify_flow_context(flow, context)

    # dynamicOpenID POSTs the signed request object alongside the same query string a plain
    # GET would carry, so the parameters are still read from request.GET.
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.GET.get("redirect_uri") != REDIRECT_URI:
            return HttpResponseBadRequest("Invalid redirect_uri")
        if not self.connector.authorization_flow:
            return HttpResponseBadRequest("No authorization flow configured")

        planner = FlowPlanner(self.connector.authorization_flow)
        planner.allow_empty_flows = True
        context = {
            PLAN_CONTEXT_PSSO: {
                "state": request.GET.get("state", ""),
                "connector": self.connector,
                "device_connection": self.device_connection,
                "scope": request.GET.get("scope", "openid profile email"),
            }
        }
        if login_hint := request.GET.get(QS_LOGIN_HINT):
            context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = login_hint
        try:
            plan = planner.plan(request, context)
        except FlowNonApplicableException:
            return self.handle_no_permission_authenticated()

        plan.append_stage(in_memory_stage(PSSOAuthFulfillmentStage))
        return plan.to_redirect(request, self.connector.authorization_flow)


class PSSOAuthFulfillmentStage(StageView):
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        psso: dict = self.executor.plan.context.pop(PLAN_CONTEXT_PSSO)
        auth_code = AppleAuthorizationCode.objects.create(
            user=request.user,
            connector=psso["connector"],
            device_connection=psso["device_connection"],
            state=psso["state"],
            scope=psso["scope"],
            expires=now() + timedelta(minutes=5),
        )
        params = {"code": auth_code.code}
        if psso["state"]:
            params["state"] = psso["state"]
        return HttpResponseRedirectScheme(
            f"{REDIRECT_URI}?{urlencode(params)}",
            allowed_schemes=["com.apple.platformsso"],
        )
