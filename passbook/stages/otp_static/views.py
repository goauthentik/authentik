"""otp Static view Tokens"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken

from passbook.audit.models import Event


class UserSettingsView(LoginRequiredMixin, TemplateView):
    """View for user settings to control OTP"""

    template_name = "stages/otp_static/user_settings.html"

    # TODO: Check if OTP Stage exists and applies to user
    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        static_devices = StaticDevice.objects.filter(
            user=self.request.user, confirmed=True
        )
        kwargs["state"] = static_devices.exists()
        if static_devices.exists():
            kwargs["tokens"] = StaticToken.objects.filter(device=static_devices.first())
        return kwargs


class DisableView(LoginRequiredMixin, View):
    """Disable Static Tokens for user"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Delete all the devices for user"""
        devices = StaticDevice.objects.filter(user=request.user, confirmed=True)
        devices.delete()
        messages.success(request, "Successfully disabled Static OTP Tokens")
        # Create event with email notification
        Event.new(
            "static_otp_disable", message="User disabled Static OTP Tokens."
        ).from_http(request)
        return redirect("passbook_stages_otp:otp-user-settings")
