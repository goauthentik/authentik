from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.views import View
from django.views.generic import FormView, TemplateView
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.contrib import messages
from passbook.audit.models import Event, EventAction
from django.shortcuts import redirect

from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.otp_time.models import OTPTimeStage


class UserSettingsView(LoginRequiredMixin, TemplateView):
    """View for user settings to control OTP"""

    template_name = "stages/otp_time/user_settings.html"

    # TODO: Check if OTP Stage exists and applies to user
    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        totp_devices = TOTPDevice.objects.filter(user=self.request.user, confirmed=True)
        kwargs["state"] = totp_devices.exists()
        return kwargs


class DisableView(LoginRequiredMixin, View):
    """Disable TOTP for user"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Delete all the devices for user"""
        totp = TOTPDevice.objects.filter(user=request.user, confirmed=True)
        totp.delete()
        messages.success(request, "Successfully disabled Time-based OTP")
        # Create event with email notification
        Event.new(EventAction.CUSTOM, message="User disabled Time-based OTP.").from_http(request)
        return redirect("passbook_stages_otp:otp-user-settings")
