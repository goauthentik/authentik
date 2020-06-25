"""passbook OIDC Views"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views import View
from oidc_provider.lib.endpoints.authorize import AuthorizeEndpoint
from oidc_provider.lib.utils.common import get_issuer, get_site_url
from oidc_provider.models import ResponseType
from oidc_provider.views import AuthorizeView
from structlog import get_logger

from passbook.core.models import Application
from passbook.core.views.access import AccessMixin
from passbook.flows.models import in_memory_stage
from passbook.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_SSO,
    FlowPlan,
    FlowPlanner,
)
from passbook.flows.stage import StageView
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.urls import redirect_with_qs
from passbook.providers.oidc.models import OpenIDProvider
from passbook.stages.consent.stage import PLAN_CONTEXT_CONSENT_TEMPLATE

LOGGER = get_logger()

PLAN_CONTEXT_PARAMS = "params"
PLAN_CONTEXT_SCOPES = "scopes"


class AuthorizationFlowInitView(AccessMixin, LoginRequiredMixin, View):
    """OIDC Flow initializer, checks access to application and starts flow"""

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check access to application, start FlowPLanner, return to flow executor shell"""
        client_id = request.GET.get("client_id")
        provider = get_object_or_404(OpenIDProvider, oidc_client__client_id=client_id)
        try:
            application = self.provider_to_application(provider)
        except Application.DoesNotExist:
            return redirect("passbook_providers_oauth:oauth2-permission-denied")
        # Check permissions
        result = self.user_has_access(application, request.user)
        if not result.passing:
            for policy_message in result.messages:
                messages.error(request, policy_message)
            return redirect("passbook_providers_oauth:oauth2-permission-denied")
        # Extract params so we can save them in the plan context
        endpoint = AuthorizeEndpoint(request)
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(provider.authorization_flow)
        # planner.use_cache = False
        planner.allow_empty_flows = True
        plan = planner.plan(
            self.request,
            {
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_APPLICATION: application,
                PLAN_CONTEXT_PARAMS: endpoint.params,
                PLAN_CONTEXT_SCOPES: endpoint.get_scopes_information(),
                PLAN_CONTEXT_CONSENT_TEMPLATE: "providers/oidc/consent.html",
            },
        )
        plan.append(in_memory_stage(OIDCStage))
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "passbook_flows:flow-executor-shell",
            self.request.GET,
            flow_slug=provider.authorization_flow.slug,
        )


class FlowAuthorizeEndpoint(AuthorizeEndpoint):
    """Restore params from flow context"""

    def _extract_params(self):
        plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
        self.params = plan.context[PLAN_CONTEXT_PARAMS]


class OIDCStage(AuthorizeView, StageView):
    """Finall stage, restores params from Flow."""

    authorize_endpoint_class = FlowAuthorizeEndpoint


class ProviderInfoView(View):
    """Custom ProviderInfo View which shows our URLs instead"""

    # pylint: disable=unused-argument
    def get(self, request, *args, **kwargs):
        """Custom ProviderInfo View which shows our URLs instead"""
        dic = dict()

        site_url = get_site_url(request=request)
        dic["issuer"] = get_issuer(site_url=site_url, request=request)

        dic["authorization_endpoint"] = site_url + reverse(
            "passbook_providers_oidc:authorize"
        )
        dic["token_endpoint"] = site_url + reverse("oidc_provider:token")
        dic["userinfo_endpoint"] = site_url + reverse("oidc_provider:userinfo")
        dic["end_session_endpoint"] = site_url + reverse("oidc_provider:end-session")
        dic["introspection_endpoint"] = site_url + reverse(
            "oidc_provider:token-introspection"
        )

        types_supported = [
            response_type.value for response_type in ResponseType.objects.all()
        ]
        dic["response_types_supported"] = types_supported

        dic["jwks_uri"] = site_url + reverse("oidc_provider:jwks")

        dic["id_token_signing_alg_values_supported"] = ["HS256", "RS256"]

        # See: http://openid.net/specs/openid-connect-core-1_0.html#SubjectIDTypes
        dic["subject_types_supported"] = ["public"]

        dic["token_endpoint_auth_methods_supported"] = [
            "client_secret_post",
            "client_secret_basic",
        ]

        response = JsonResponse(dic)
        response["Access-Control-Allow-Origin"] = "*"

        return response
