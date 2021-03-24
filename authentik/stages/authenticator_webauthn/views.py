"""webauthn views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http.response import Http404
from django.utils.translation import gettext as _
from django.views.generic import UpdateView

from authentik.stages.authenticator_webauthn.forms import DeviceEditForm
from authentik.stages.authenticator_webauthn.models import (
    WebAuthnDevice,
)

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
