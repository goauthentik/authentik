"""app views"""

from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import View

from authentik.core.models import Application
from authentik.flows.challenge import (
    ChallengeResponse,
    HttpChallengeResponse,
    RedirectChallenge,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import FlowDesignation, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlanner
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import (
    SESSION_KEY_APPLICATION_PRE,
    ToDefaultFlow,
)
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
)


class RedirectToAppLaunch(View):
    """Application launch view, redirect to the launch URL"""

    def dispatch(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        app = get_object_or_404(Application, slug=application_slug)
        # Check here if the application has any launch URL set, if not 404
        launch = app.get_launch_url()
        if not launch:
            raise Http404
        # Check if we're authenticated already, saves us the flow run
        if request.user.is_authenticated:
            return HttpResponseRedirect(app.get_launch_url(request.user))
        self.request.session[SESSION_KEY_APPLICATION_PRE] = app
        # otherwise, do a custom flow plan that includes the application that's
        # being accessed, to improve usability
        flow = ToDefaultFlow(request=request, designation=FlowDesignation.AUTHENTICATION).get_flow()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                request,
                {
                    PLAN_CONTEXT_APPLICATION: app,
                    PLAN_CONTEXT_CONSENT_HEADER: _("You're about to sign into %(application)s.")
                    % {"application": app.name},
                    PLAN_CONTEXT_CONSENT_PERMISSIONS: [],
                },
            )
        except FlowNonApplicableException:
            raise Http404 from None
        plan.append_stage(in_memory_stage(RedirectToAppStage))
        return plan.to_redirect(request, flow)


class RedirectToAppStage(ChallengeStageView):
    """Final stage to be inserted after the user logs in"""

    def get_challenge(self, *args, **kwargs) -> RedirectChallenge:
        app = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        launch = app.get_launch_url(self.get_pending_user())
        # sanity check to ensure launch is still set
        if not launch:
            raise Http404
        return RedirectChallenge(
            instance={
                "to": launch,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return HttpChallengeResponse(self.get_challenge())
