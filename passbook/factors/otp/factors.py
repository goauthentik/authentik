"""OTP Factor logic"""
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.generic import FormView
from django_otp import match_token, user_has_device
from structlog import get_logger

from passbook.factors.otp.forms import OTPVerifyForm
from passbook.factors.otp.views import OTP_SETTING_UP_KEY, EnableView
from passbook.flows.factor_base import AuthenticationFactor
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER

LOGGER = get_logger()


class OTPFactor(FormView, AuthenticationFactor):
    """OTP Factor View"""

    template_name = "otp/factor.html"
    form_class = OTPVerifyForm

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["title"] = _("Enter Verification Code")
        return kwargs

    def get(self, request, *args, **kwargs):
        """Check if User has OTP enabled and if OTP is enforced"""
        pending_user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        if not user_has_device(pending_user):
            LOGGER.debug("User doesn't have OTP Setup.")
            if self.executor.current_factor.enforced:
                # Redirect to setup view
                LOGGER.debug("OTP is enforced, redirecting to setup")
                request.user = pending_user
                messages.info(request, _("OTP is enforced. Please setup OTP."))
                return EnableView.as_view()(request)
            LOGGER.debug("OTP is not enforced, skipping form")
            return self.executor.user_ok()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Check if setup is in progress and redirect to EnableView"""
        if OTP_SETTING_UP_KEY in request.session:
            LOGGER.debug("Passing POST to EnableView")
            request.user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
            return EnableView.as_view()(request)
        return super().post(self, request, *args, **kwargs)

    def form_valid(self, form: OTPVerifyForm):
        """Verify OTP Token"""
        device = match_token(
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER],
            form.cleaned_data.get("code"),
        )
        if device:
            return self.executor.factor_ok()
        messages.error(self.request, _("Invalid OTP."))
        return self.form_invalid(form)
