"""WebAuthn stage"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import FormView
from structlog.stdlib import get_logger

from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.stages.webauthn.models import WebAuthnDevice

LOGGER = get_logger()

SESSION_KEY_WEBAUTHN_AUTHENTICATED = "authentik_stages_webauthn_authenticated"


class WebAuthnStageView(FormView, StageView):
    """WebAuthn stage"""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()
        devices = WebAuthnDevice.objects.filter(user=user)
        # If the current user is logged in already, or the pending user
        # has no devices, show setup
        if self.request.user == user:
            # Because the user is already authenticated, skip the later check
            self.request.session[SESSION_KEY_WEBAUTHN_AUTHENTICATED] = True
            return render(request, "stages/webauthn/setup.html")
        if not devices.exists():
            return self.executor.stage_ok()
        self.request.session[SESSION_KEY_WEBAUTHN_AUTHENTICATED] = False
        return render(request, "stages/webauthn/auth.html")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Since the client can't directly indicate when a stage is done,
        we use the post handler for this"""
        if request.session.pop(SESSION_KEY_WEBAUTHN_AUTHENTICATED, False):
            return self.executor.stage_ok()
        return self.executor.stage_invalid()
