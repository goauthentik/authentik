from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.admin.sites import AdminSite

from .forms import OTPAuthenticationFormMixin


def _admin_template_for_django_version():
    """
    Returns the most appropriate Django login template available.

    In the past, we've had more version-specific templates. Perhaps this will
    be true again in the future. For now, the Django 1.11 version is suitable
    even with the most recent Django version.
    """
    return "otp/admin111/login.html"


class OTPAdminAuthenticationForm(AdminAuthenticationForm, OTPAuthenticationFormMixin):
    """
    An :class:`~django.contrib.admin.forms.AdminAuthenticationForm` subclass
    that solicits an OTP token. This has the same behavior as
    :class:`~django_otp.forms.OTPAuthenticationForm`.
    """

    otp_device = forms.CharField(required=False, widget=forms.Select)
    otp_token = forms.CharField(required=False)

    # This is a placeholder field that allows us to detect when the user clicks
    # the otp_challenge submit button.
    otp_challenge = forms.CharField(required=False)

    def clean(self):
        self.cleaned_data = super().clean()
        self.clean_otp(self.get_user())

        return self.cleaned_data


class OTPAdminSite(AdminSite):
    """
    This is an :class:`~django.contrib.admin.AdminSite` subclass that requires
    two-factor authentication. Only users that can be verified by a registered
    OTP device will be authorized for this admin site. Unverified users will be
    treated as if :attr:`~django.contrib.auth.models.User.is_staff` is
    ``False``.
    """

    #: The default instance name of this admin site. You should instantiate
    #: this class as ``OTPAdminSite(OTPAdminSite.name)`` to make sure the admin
    #: templates render the correct URLs.
    name = "otpadmin"

    login_form = OTPAdminAuthenticationForm

    #: We automatically select a modified login template based on your Django
    #: version. If it doesn't look right, your version may not be supported, in
    #: which case feel free to replace it.
    login_template = _admin_template_for_django_version()

    def __init__(self, name="otpadmin"):
        super().__init__(name)

    def has_permission(self, request):
        """
        In addition to the default requirements, this only allows access to
        users who have been verified by a registered OTP device.
        """
        return super().has_permission(request) and request.user.is_verified()
