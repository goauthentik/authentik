"""webauthn views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.http.response import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.lib.templatetags.authentik_utils import avatar
from authentik.stages.authenticator_webauthn.models import (
    AuthenticateWebAuthnStage,
    WebAuthnDevice,
)
from authentik.stages.authenticator_webauthn.stage import (
    SESSION_KEY_WEBAUTHN_AUTHENTICATED,
)
from authentik.stages.authenticator_webauthn.utils import generate_challenge

LOGGER = get_logger()
RP_ID = "localhost"
RP_NAME = "authentik"
ORIGIN = "http://localhost:8000"


class UserSettingsView(LoginRequiredMixin, TemplateView):
    """View for user settings to control WebAuthn devices"""

    template_name = "stages/authenticator_webauthn/user_settings.html"

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["devices"] = WebAuthnDevice.objects.filter(user=self.request.user)
        stage = get_object_or_404(
            AuthenticateWebAuthnStage, pk=self.kwargs["stage_uuid"]
        )
        kwargs["stage"] = stage
        return kwargs
