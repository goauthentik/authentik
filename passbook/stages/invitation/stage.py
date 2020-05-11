"""invitation stage logic"""
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from passbook.flows.stage import AuthenticationStage
from passbook.stages.invitation.models import Invitation, InvitationStage
from passbook.stages.prompt.stage import PLAN_CONTEXT_PROMPT

INVITATION_TOKEN_KEY = "token"


class InvitationStageView(AuthenticationStage):
    """Finalise Authentication flow by logging the user in"""

    def get(self, request: HttpRequest) -> HttpResponse:
        stage: InvitationStage = self.executor.current_stage
        if INVITATION_TOKEN_KEY not in request.GET:
            # No Invitation was given, raise error or continue
            if stage.continue_flow_without_invitation:
                return self.executor.stage_ok()
            return self.executor.stage_invalid()

        token = request.GET[INVITATION_TOKEN_KEY]
        invite: Invitation = get_object_or_404(Invitation, pk=token)
        self.executor.plan.context[PLAN_CONTEXT_PROMPT] = invite.fixed_data
        return self.executor.stage_ok()
