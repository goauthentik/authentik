from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from authentik.core.models import Application
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.constants import (
    WS_FED_ACTION_SIGN_IN,
    WS_FED_ACTION_SIGN_OUT,
)
from authentik.enterprise.providers.ws_federation.processors.sign_in import (
    SignInProcessor,
)
from authentik.flows.challenge import (
    PLAN_CONTEXT_TITLE,
    AutosubmitChallenge,
    AutoSubmitChallengeResponse,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_SSO, FlowPlanner
from authentik.flows.stage import ChallengeStageView
from authentik.policies.views import PolicyAccessView
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
)

PLAN_CONTEXT_WS_FED_REQUEST = "authentik/providers/ws_federation/request"


class WSFedEntryView(PolicyAccessView):
    def resolve_provider_application(self):
        self.action = self.request.GET.get("wa")
        self.realm = self.request.GET.get("wtrealm")
        self.wreply = self.request.GET.get("wreply")
        self.wctx = self.request.GET.get("wctx", "")

        self.application = get_object_or_404(Application, slug=self.realm)
        self.provider: WSFederationProvider = get_object_or_404(
            WSFederationProvider, pk=self.application.provider_id
        )

    def get(self, request: HttpRequest) -> HttpResponse:
        if self.action == WS_FED_ACTION_SIGN_IN:
            return self.ws_fed_sign_in()
        elif self.action == WS_FED_ACTION_SIGN_OUT:
            return HttpResponse("Unsupported WS-Federation action", status=400)
        else:
            return HttpResponse("Unsupported WS-Federation action", status=400)

    def ws_fed_sign_in(self) -> HttpResponse:
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        try:
            req = SignInProcessor(self.provider).parse(self.request)

            plan = planner.plan(
                self.request,
                {
                    PLAN_CONTEXT_SSO: True,
                    PLAN_CONTEXT_APPLICATION: self.application,
                    PLAN_CONTEXT_CONSENT_HEADER: _("You're about to sign into %(application)s.")
                    % {"application": self.application.name},
                    PLAN_CONTEXT_CONSENT_PERMISSIONS: [],
                    PLAN_CONTEXT_WS_FED_REQUEST: req,
                },
            )
        except FlowNonApplicableException:
            raise Http404 from None
        plan.append_stage(in_memory_stage(WSFedFlowFinalView))
        return plan.to_redirect(
            self.request,
            self.provider.authorization_flow,
        )


class WSFedFlowFinalView(ChallengeStageView):
    response_class = AutoSubmitChallengeResponse

    def get_challenge(self, *args, **kwargs):
        application: Application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        provider: WSFederationProvider = get_object_or_404(
            WSFederationProvider, pk=application.provider_id
        )
        if PLAN_CONTEXT_WS_FED_REQUEST not in self.executor.plan.context:
            self.logger.warning("No WS-Fed request in context")
            return self.executor.stage_invalid()
        proc = SignInProcessor(provider, self.request)
        response = proc.response(self.executor.plan.context[PLAN_CONTEXT_WS_FED_REQUEST])
        return AutosubmitChallenge(
            data={
                "component": "ak-stage-autosubmit",
                "title": self.executor.plan.context.get(
                    PLAN_CONTEXT_TITLE,
                    _("Redirecting to {app}...".format_map({"app": application.name})),
                ),
                "url": provider.acs_url,
                "attrs": response,
            },
        )
