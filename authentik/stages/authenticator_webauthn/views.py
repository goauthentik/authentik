"""webauthn views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, UpdateView

from authentik.admin.views.utils import DeleteMessageView
from authentik.stages.authenticator_webauthn.forms import DeviceEditForm
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


class DeviceUpdateView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    """Update device"""

    model = WebAuthnDevice
    form_class = DeviceEditForm
    template_name = "generic/update.html"
    success_url = "/"
    success_message = _("Successfully updated Device")

    def get_object(self) -> WebAuthnDevice:
        device: WebAuthnDevice = super().get_object()
        if device.user != self.request.user:
            raise Http404
        return device


class DeviceDeleteView(LoginRequiredMixin, DeleteMessageView):
    """Delete device"""

    model = WebAuthnDevice
    template_name = "generic/delete.html"
    success_url = "/"
    success_message = _("Successfully deleted Device")

    def get_object(self) -> WebAuthnDevice:
        device: WebAuthnDevice = super().get_object()
        if device.user != self.request.user:
            raise Http404
        return device
