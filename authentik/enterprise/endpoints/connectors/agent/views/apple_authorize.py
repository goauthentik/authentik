from datetime import timedelta

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
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
from authentik.endpoints.models import Device
from authentik.enterprise.license import LicenseKey
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

connector_id = "8799c408-8631-44e9-be58-5524b726084a"
device_id = "331cc865-5bcd-4a82-b079-c07726f60c82"


class PSSORedirect(HttpResponseRedirect):
    allowed_schemes = ["com.apple.platformsso", "com.apple.PlatformSSO"]


class AppleAuthorizePreauthView(View):
    """Platform SSO federation pre-authentication discovery endpoint.

    Called by Platform SSO before it loads the authorization web view (dynamicOpenID
    federation, see federationUserPreauthenticationURL). Generates the `state` value here
    since it's the only point in the flow before the web view is a plain, unauthenticated
    HTTP request; AppleAuthorizeView threads that same state through to the final redirect
    so Platform SSO's own CSRF check on the callback has something real to validate against.
    https://developer.apple.com/documentation/authenticationservices/implementing-web-based-authentication
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        if not LicenseKey.get_total().status().is_valid:
            return HttpResponseBadRequest("Enterprise required to access this feature.")
        params = {
            "state": get_random_string(32),
            "redirect_uri": "com.apple.PlatformSSO://callback",
        }
        login_hint = request.GET.get("user")
        if login_hint:
            params[QS_LOGIN_HINT] = login_hint
        authorization_url = request.build_absolute_uri(
            reverse("authentik_enterprise_endpoints_connectors_agent:psso-authorize")
        )
        return JsonResponse({"authorization_url": authorization_url + "?" + urlencode(params)})


@method_decorator(csrf_exempt, name="dispatch")
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

    def verify_request_jwt(self, request: HttpRequest) -> None:
        """dynamicOpenID federation POSTs a device-signed JWT ('request' form field, typ
        platformsso-authorization-request+jwt) alongside the same query string a plain GET
        would carry. state/redirect_uri/scope below still come from the query string either
        way; this only checks the signature against the device's known signing key, as a
        defense-in-depth signal that the POST really came from this device.
        https://developer.apple.com/documentation/authenticationservices/implementing-web-based-authentication
        """
        assertion = request.POST.get("request")
        if not assertion:
            return
        try:
            get_unverified_header(assertion)
            device_connection = AgentDeviceConnection.objects.filter(
                device=self.device, connector=self.connector
            ).first()
            if not device_connection or not device_connection.apple_signing_key:
                LOGGER.warning(
                    "Platform SSO authorization request JWT present but no device "
                    "signing key on file"
                )
                return
            decode(assertion, device_connection.apple_signing_key, algorithms=["ES256"])
        except PyJWTError as exc:
            LOGGER.warning("Platform SSO authorization request JWT failed verification", exc=exc)

    def get(self, request: HttpRequest) -> HttpResponse:
        self.verify_request_jwt(request)
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
            PLAN_CONTEXT_PSSO_SCOPE: request.GET.get("scope", "openid profile email"),
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

    # dynamicOpenID federation POSTs a signed request object instead of a plain GET; the
    # query string it's built from is identical either way (request.GET reads the URL's
    # query string regardless of HTTP method), so the same handler covers both.
    post = get


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
