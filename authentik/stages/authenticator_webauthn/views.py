"""webauthn views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from authentik.stages.authenticator_webauthn.models import (
    AuthenticateWebAuthnStage,
    WebAuthnDevice,
)


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
