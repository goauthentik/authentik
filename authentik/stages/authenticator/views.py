from functools import partial

from django.contrib.auth import BACKEND_SESSION_KEY
from django.contrib.auth import views as auth_views
from django.utils.functional import cached_property

from authentik.stages.authenticator.forms import OTPAuthenticationForm, OTPTokenForm


class LoginView(auth_views.LoginView):
    """
    This is a replacement for :class:`django.contrib.auth.views.LoginView` that
    requires two-factor authentication. It's slightly clever: if the user is
    already authenticated but not verified, it will only ask the user for their
    OTP token. If the user is anonymous or is already verified by an OTP
    device, it will use the full username/password/token form. In order to use
    this, you must supply a template that is compatible with both
    :class:`~django_otp.forms.OTPAuthenticationForm` and
    :class:`~django_otp.forms.OTPTokenForm`. This is a good view for
    :setting:`OTP_LOGIN_URL`.

    """

    otp_authentication_form = OTPAuthenticationForm
    otp_token_form = OTPTokenForm

    @cached_property
    def authentication_form(self):
        user = self.request.user
        if user.is_anonymous or user.is_verified():
            form = self.otp_authentication_form
        else:
            form = partial(self.otp_token_form, user)

        return form

    def form_valid(self, form):
        # OTPTokenForm does not call authenticate(), so we may need to populate
        # user.backend ourselves to keep login() happy.
        user = form.get_user()
        if not hasattr(user, "backend"):
            user.backend = self.request.session[BACKEND_SESSION_KEY]

        return super().form_valid(form)


# Backwards compatibility.
login = LoginView.as_view()
