from django.http import HttpRequest, HttpResponse

from authentik.enterprise.requests.grants import (
    GrantExpiry,
    create_grant_request,
)
from authentik.flows.stage import StageView
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_GRANT_REQUESTED_PBMS = "goauthentik.io/requests/requested-pbms"
PLAN_CONTEXT_GRANT_PENDING_EXPIRY = "goauthentik.io/requests/pending-expiry"
PLAN_CONTEXT_GRANT_MAX_EXPIRY = "goauthentik.io/requests/max-expiry"
PLAN_CONTEXT_GRANT_REQUESTED_EXPIRY = "goauthentik.io/requests/requested-expiry"


class GrantRequestFinalStageView(StageView):

    def get(self, request: HttpRequest) -> HttpResponse:
        user = self.get_pending_user()
        pbms = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_REQUESTED_PBMS)
        pending_expiry = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_PENDING_EXPIRY)
        max_expiry = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_MAX_EXPIRY)
        requested_expiry = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_REQUESTED_EXPIRY)
        # Enforce the configured maximum here, at persistence time, rather than
        # earlier in create() -- a stage in the flow may have changed the requested
        # duration since, so the ceiling can only be safely applied at the end.
        granted_expiry_candidates = [timedelta_from_string(max_expiry)]
        if requested_expiry:
            granted_expiry_candidates.append(timedelta_from_string(requested_expiry))
        create_grant_request(
            request,
            created_by=user,
            pbms=pbms,
            requester_data=self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}),
            expiry=GrantExpiry(
                pending=timedelta_from_string(pending_expiry),
                granted=min(granted_expiry_candidates),
            ),
        )
        return self.executor.stage_ok()

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
