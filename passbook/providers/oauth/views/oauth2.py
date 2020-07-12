"""passbook OAuth2 Views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import View
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.views.base import AuthorizationView
from structlog import get_logger

from passbook.audit.models import Event, EventAction
from passbook.core.models import Application
from passbook.flows.models import in_memory_stage
from passbook.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from passbook.flows.stage import StageView
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.urls import redirect_with_qs
from passbook.policies.mixins import PolicyAccessMixin
from passbook.providers.oauth.models import OAuth2Provider
from passbook.stages.consent.stage import PLAN_CONTEXT_CONSENT_TEMPLATE

LOGGER = get_logger()

PLAN_CONTEXT_CLIENT_ID = "client_id"
PLAN_CONTEXT_REDIRECT_URI = "redirect_uri"
PLAN_CONTEXT_RESPONSE_TYPE = "response_type"
PLAN_CONTEXT_STATE = "state"

PLAN_CONTEXT_CODE_CHALLENGE = "code_challenge"
PLAN_CONTEXT_CODE_CHALLENGE_METHOD = "code_challenge_method"
PLAN_CONTEXT_SCOPE = "scope"
PLAN_CONTEXT_NONCE = "nonce"
PLAN_CONTEXT_SCOPE_DESCRIPTION = "scope_descriptions"


class AuthorizationFlowInitView(PolicyAccessMixin, LoginRequiredMixin, View):
    """OAuth2 Flow initializer, checks access to application and starts flow"""

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check access to application, start FlowPLanner, return to flow executor shell"""
        client_id = request.GET.get("client_id")
        provider = get_object_or_404(OAuth2Provider, client_id=client_id)
        try:
            application = self.provider_to_application(provider)
        except Application.DoesNotExist:
            return self.handle_no_permission_authorized()
        # Check if user is unauthenticated, so we pass the application
        # for the identification stage
        if not request.user.is_authenticated:
            return self.handle_no_permission(application)
        # Check permissions
        result = self.user_has_access(application)
        if not result.passing:
            return self.handle_no_permission_authorized()
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(provider.authorization_flow)
        planner.allow_empty_flows = True
        # Save scope descriptions
        scopes = request.GET.get(PLAN_CONTEXT_SCOPE)
        all_scopes = get_scopes_backend().get_all_scopes()

        plan = planner.plan(
            self.request,
            {
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_APPLICATION: application,
                PLAN_CONTEXT_CLIENT_ID: client_id,
                PLAN_CONTEXT_REDIRECT_URI: request.GET.get(PLAN_CONTEXT_REDIRECT_URI),
                PLAN_CONTEXT_RESPONSE_TYPE: request.GET.get(PLAN_CONTEXT_RESPONSE_TYPE),
                PLAN_CONTEXT_STATE: request.GET.get(PLAN_CONTEXT_STATE),
                PLAN_CONTEXT_SCOPE: scopes,
                PLAN_CONTEXT_NONCE: request.GET.get(PLAN_CONTEXT_NONCE),
                PLAN_CONTEXT_SCOPE_DESCRIPTION: [
                    all_scopes[scope] for scope in scopes.split(" ")
                ],
                PLAN_CONTEXT_CONSENT_TEMPLATE: "providers/oauth/consent.html",
            },
        )

        plan.append(in_memory_stage(OAuth2Stage))
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "passbook_flows:flow-executor-shell",
            self.request.GET,
            flow_slug=provider.authorization_flow.slug,
        )


class OAuth2Stage(AuthorizationView, StageView):
    """OAuth2 Stage, dynamically injected into the plan"""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Last stage in flow, finalizes OAuth Response and redirects to Client"""
        application: Application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        provider: OAuth2Provider = application.provider

        Event.new(
            EventAction.AUTHORIZE_APPLICATION, authorized_application=application,
        ).from_http(self.request)

        credentials = {
            "client_id": self.executor.plan.context[PLAN_CONTEXT_CLIENT_ID],
            "redirect_uri": self.executor.plan.context[PLAN_CONTEXT_REDIRECT_URI],
            "response_type": self.executor.plan.context.get(
                PLAN_CONTEXT_RESPONSE_TYPE, None
            ),
            "state": self.executor.plan.context.get(PLAN_CONTEXT_STATE, None),
            "nonce": self.executor.plan.context.get(PLAN_CONTEXT_NONCE, None),
        }
        if self.executor.plan.context.get(PLAN_CONTEXT_CODE_CHALLENGE, False):
            credentials[PLAN_CONTEXT_CODE_CHALLENGE] = self.executor.plan.context.get(
                PLAN_CONTEXT_CODE_CHALLENGE
            )
        if self.executor.plan.context.get(PLAN_CONTEXT_CODE_CHALLENGE_METHOD, False):
            credentials[
                PLAN_CONTEXT_CODE_CHALLENGE_METHOD
            ] = self.executor.plan.context.get(PLAN_CONTEXT_CODE_CHALLENGE_METHOD)
        scopes = self.executor.plan.context.get(PLAN_CONTEXT_SCOPE)

        try:
            uri, _headers, _body, _status = self.create_authorization_response(
                request=self.request,
                scopes=scopes,
                credentials=credentials,
                allow=True,
            )
            LOGGER.debug("Success url for the request: {0}".format(uri))
        except OAuthToolkitError as error:
            return self.error_response(error, provider)

        self.executor.stage_ok()
        return HttpResponseRedirect(self.redirect(uri, provider).url)
