"""WebAuthn stage"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import FormView
from structlog.stdlib import get_logger

from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.stages.webauthn.models import WebAuthnDevice

LOGGER = get_logger()


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
            return render(request, "stages/webauthn/setup.html")
        if not devices.exists():
            return self.executor.stage_ok()
        return render(request, "stages/webauthn/auth.html")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Since the client can't directly indicate when a stage is done,
        we use the post handler for this"""
        return self.executor.stage_ok()
