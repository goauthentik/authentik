"""invitation stage logic"""
from copy import deepcopy
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from authentik.flows.stage import StageView
from authentik.flows.views import SESSION_KEY_GET
from authentik.stages.invitation.models import Invitation, InvitationStage
from authentik.stages.invitation.signals import invitation_used
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

INVITATION_TOKEN_KEY = "token"  # nosec
INVITATION_IN_EFFECT = "invitation_in_effect"


class InvitationStageView(StageView):
    """Finalise Authentication flow by logging the user in"""

    def get_token(self) -> Optional[str]:
        """Get token from saved get-arguments or prompt_data"""
        if INVITATION_TOKEN_KEY in self.request.session.get(SESSION_KEY_GET, {}):
            return self.request.session[SESSION_KEY_GET][INVITATION_TOKEN_KEY]
        if INVITATION_TOKEN_KEY in self.executor.plan.context.get(
            PLAN_CONTEXT_PROMPT, {}
        ):
            return self.executor.plan.context[PLAN_CONTEXT_PROMPT][INVITATION_TOKEN_KEY]
        return None

    def get(self, request: HttpRequest) -> HttpResponse:
        """Apply data to the current flow based on a URL"""
        stage: InvitationStage = self.executor.current_stage
        token = self.get_token()
        if not token:
            # No Invitation was given, raise error or continue
            if stage.continue_flow_without_invitation:
                return self.executor.stage_ok()
            return self.executor.stage_invalid()

        invite: Invitation = get_object_or_404(Invitation, pk=token)
        self.executor.plan.context[PLAN_CONTEXT_PROMPT] = deepcopy(invite.fixed_data)
        self.executor.plan.context[INVITATION_IN_EFFECT] = True
        invitation_used.send(sender=self, request=request, invitation=invite)
        if invite.single_use:
            invite.delete()
        return self.executor.stage_ok()
