"""invitation stage logic"""
from typing import Optional

from deepmerge import always_merger
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBadRequest

from authentik.flows.models import in_memory_stage
from authentik.flows.stage import StageView
from authentik.flows.views.executor import SESSION_KEY_GET
from authentik.stages.invitation.models import Invitation, InvitationStage
from authentik.stages.invitation.signals import invitation_used
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

INVITATION_TOKEN_KEY_CONTEXT = "token"  # nosec
INVITATION_TOKEN_KEY = "itoken"  # nosec
INVITATION_IN_EFFECT = "invitation_in_effect"
INVITATION = "invitation"


class InvitationStageView(StageView):
    """Finalise Authentication flow by logging the user in"""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)

    def get_token(self) -> Optional[str]:
        """Get token from saved get-arguments or prompt_data"""
        # Check for ?token= and ?itoken=
        if INVITATION_TOKEN_KEY in self.request.session.get(SESSION_KEY_GET, {}):
            return self.request.session[SESSION_KEY_GET][INVITATION_TOKEN_KEY]
        if INVITATION_TOKEN_KEY_CONTEXT in self.request.session.get(SESSION_KEY_GET, {}):
            return self.request.session[SESSION_KEY_GET][INVITATION_TOKEN_KEY_CONTEXT]
        # Check for {'token': ''} in the context
        if INVITATION_TOKEN_KEY_CONTEXT in self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}):
            return self.executor.plan.context[PLAN_CONTEXT_PROMPT][INVITATION_TOKEN_KEY_CONTEXT]
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

        invite: Invitation = Invitation.objects.filter(pk=token).first()
        if not invite:
            self.logger.debug("invalid invitation", token=token)
            if stage.continue_flow_without_invitation:
                return self.executor.stage_ok()
            return self.executor.stage_invalid()
        self.executor.plan.context[INVITATION_IN_EFFECT] = True
        self.executor.plan.context[INVITATION] = invite

        context = {}
        always_merger.merge(context, self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}))
        always_merger.merge(context, invite.fixed_data)
        self.executor.plan.context[PLAN_CONTEXT_PROMPT] = context

        invitation_used.send(sender=self, request=request, invitation=invite)
        if invite.single_use:
            self.executor.plan.append_stage(in_memory_stage(InvitationFinalStageView))
        return self.executor.stage_ok()


class InvitationFinalStageView(StageView):
    """Final stage which is injected by invitation stage. Deletes
    the used invitation."""

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Call get as this request may be called with post"""
        return self.get(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Delete invitation if single_use is active"""
        invitation: Invitation = self.executor.plan.context.get(INVITATION, None)
        if not invitation:
            self.logger.warning("InvitationFinalStageView stage called without invitation")
            return HttpResponseBadRequest
        token = invitation.invite_uuid.hex
        if invitation.single_use:
            invitation.delete()
            self.logger.debug("Deleted invitation", token=token)
        del self.executor.plan.context[INVITATION]
        return self.executor.stage_ok()
