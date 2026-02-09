from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import Application, AuthenticatedSession
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.constants import (
    WS_FED_ACTION_SIGN_IN,
    WS_FED_ACTION_SIGN_OUT,
)
from authentik.enterprise.providers.ws_federation.processors.sign_in import (
    SignInProcessor,
    SignInRequest,
)
from authentik.enterprise.providers.ws_federation.processors.sign_out import SignOutRequest
from authentik.flows.challenge import (
    PLAN_CONTEXT_TITLE,
    AutosubmitChallenge,
    AutoSubmitChallengeResponse,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_SSO, FlowPlanner
from authentik.flows.stage import ChallengeStageView, SessionEndStage
from authentik.lib.views import bad_request_message
from authentik.policies.views import PolicyAccessView, RequestValidationError
from authentik.providers.saml.models import SAMLSession
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
)

PLAN_CONTEXT_WS_FED_REQUEST = "authentik/providers/ws_federation/request"
LOGGER = get_logger()


class WSFedEntryView(PolicyAccessView):
    req: SignInRequest | SignOutRequest

    def pre_permission_check(self):
        self.action = self.request.GET.get("wa")
        try:
            if self.action == WS_FED_ACTION_SIGN_IN:
                self.req = SignInRequest.parse(self.request)
            elif self.action == WS_FED_ACTION_SIGN_OUT:
                self.req = SignOutRequest.parse(self.request)
            else:
                raise RequestValidationError(
                    bad_request_message(self.request, "Invalid WS-Federation action")
                )
        except ValueError as exc:
            LOGGER.warning("Invalid WS-Fed request", exc=exc)
            raise RequestValidationError(
                bad_request_message(self.request, "Invalid WS-Federation request")
            ) from None

    def resolve_provider_application(self):
        self.application, self.provider = self.req.get_app_provider()

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if self.action == WS_FED_ACTION_SIGN_IN:
            return self.ws_fed_sign_in()
        elif self.action == WS_FED_ACTION_SIGN_OUT:
            return self.ws_fed_sign_out()
        else:
            return HttpResponse("Unsupported WS-Federation action", status=400)

    def ws_fed_sign_in(self) -> HttpResponse:
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                self.request,
                {
                    PLAN_CONTEXT_SSO: True,
                    PLAN_CONTEXT_APPLICATION: self.application,
                    PLAN_CONTEXT_CONSENT_HEADER: _("You're about to sign into %(application)s.")
                    % {"application": self.application.name},
                    PLAN_CONTEXT_CONSENT_PERMISSIONS: [],
                    PLAN_CONTEXT_WS_FED_REQUEST: self.req,
                },
            )
        except FlowNonApplicableException:
            raise Http404 from None
        plan.append_stage(in_memory_stage(WSFedFlowFinalView))
        return plan.to_redirect(
            self.request,
            self.provider.authorization_flow,
        )

    def ws_fed_sign_out(self) -> HttpResponse:
        flow = self.provider.invalidation_flow or self.request.brand.flow_invalidation

        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                self.request,
                {
                    PLAN_CONTEXT_SSO: True,
                    PLAN_CONTEXT_APPLICATION: self.application,
                    PLAN_CONTEXT_WS_FED_REQUEST: self.req,
                },
            )
        except FlowNonApplicableException:
            raise Http404 from None
        plan.append_stage(in_memory_stage(SessionEndStage))
        return plan.to_redirect(self.request, flow)


class WSFedFlowFinalView(ChallengeStageView):
    response_class = AutoSubmitChallengeResponse

    def get(self, request, *args, **kwargs):
        if PLAN_CONTEXT_WS_FED_REQUEST not in self.executor.plan.context:
            self.logger.warning("No WS-Fed request in context")
            return self.executor.stage_invalid()
        return super().get(request, *args, **kwargs)

    def get_challenge(self, *args, **kwargs):
        application: Application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        provider: WSFederationProvider = get_object_or_404(
            WSFederationProvider, pk=application.provider_id
        )
        sign_in_req: SignInRequest = self.executor.plan.context[PLAN_CONTEXT_WS_FED_REQUEST]
        proc = SignInProcessor(provider, self.request, sign_in_req)
        response = proc.response()
        saml_processor = proc.saml_processor

        # Create SAMLSession to track this login
        auth_session = AuthenticatedSession.from_request(self.request, self.request.user)
        if auth_session:
            # Since samlsessions should only exist uniquely for an active session and a provider
            # any existing combination is likely an old, dead session
            SAMLSession.objects.filter(
                session_index=saml_processor.session_index, provider=provider
            ).delete()

            SAMLSession.objects.update_or_create(
                session_index=saml_processor.session_index,
                provider=provider,
                defaults={
                    "user": self.request.user,
                    "session": auth_session,
                    "name_id": saml_processor.name_id,
                    "name_id_format": saml_processor.name_id_format,
                    "expires": saml_processor.session_not_on_or_after_datetime,
                    "expiring": True,
                },
            )
        return AutosubmitChallenge(
            data={
                "component": "ak-stage-autosubmit",
                "title": self.executor.plan.context.get(
                    PLAN_CONTEXT_TITLE,
                    _("Redirecting to {app}...".format_map({"app": application.name})),
                ),
                "url": sign_in_req.wreply,
                "attrs": response,
            },
        )
