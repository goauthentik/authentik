from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from . import devices_for_user, match_token
from .models import Device, VerifyNotAllowed


class OTPAuthenticationFormMixin:
    """
    Shared functionality for
    :class:`~django.contrib.auth.forms.AuthenticationForm` subclasses that wish
    to handle OTP tokens. Subclasses must do the following in order to use
    this:

        #. Define three additional form fields::

            otp_device = forms.CharField(required=False, widget=forms.Select)
            otp_token = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))
            otp_challenge = forms.CharField(required=False)

           - ``otp_device`` will be a select widget with all of the user's
             devices listed. Until the user has entered a valid username and
             password, this will be empty and may be omitted.
           - ``otp_token`` is where the user will enter their token.
           - ``otp_challenge`` is a placeholder field that captures an
             alternate submit button of the same name.

        #. Override :meth:`~django.forms.Form.clean` to call :meth:`clean_otp`
           after invoking the inherited :meth:`~django.forms.Form.clean`. See
           :class:`OTPAuthenticationForm` for an example.

        #. See :class:`OTPAuthenticationForm` for information about writing a
           login template for this form. The file
           ``django_otp/templates/otp/admin/login.html`` is also a useful
           example.

    You will most likely be able to use :class:`OTPAuthenticationForm`,
    :class:`~django_otp.admin.OTPAdminAuthenticationForm`, or
    :class:`OTPTokenForm` directly. If these do not suit your needs--for
    instance if your primary authentication is not by password--they should
    serve as useful examples.

    This mixin defines some error messages in
    :attr:`OTPAuthenticationFormMixin.otp_error_messages`, which can be
    overridden in subclasses (refer to the source for message codes). For
    example::

        class CustomAuthForm(OTPAuthenticationFormMixin, AuthenticationForm):
            otp_error_messages = dict(OTPAuthenticationFormMixin.otp_error_messages,
                token_required=_('Please enter your authentication code.'),
                invalid_token=_('Incorrect authentication code. Please try again.'),
            )

    """

    otp_error_messages = {
        "token_required": _("Please enter your OTP token."),
        "challenge_exception": _("Error generating challenge: {0}"),
        "not_interactive": _("The selected OTP device is not interactive"),
        "challenge_message": _("OTP Challenge: {0}"),
        "invalid_token": _("Invalid token. Please make sure you have entered it correctly."),
        "n_failed_attempts": ngettext_lazy(
            "Verification temporarily disabled because of %(failure_count)d failed attempt, please try again soon.",
            "Verification temporarily disabled because of %(failure_count)d failed attempts, please try again soon.",
            "failure_count",
        ),
        "verification_not_allowed": _("Verification of the token is currently disabled"),
    }

    def clean_otp(self, user):
        """
        Processes the ``otp_*`` fields.

        :param user: A user that has been authenticated by the first factor
            (such as a password).
        :type user: :class:`~django.contrib.auth.models.User`
        :raises: :exc:`~django.core.exceptions.ValidationError` if the user is
            not fully authenticated by an OTP token.
        """
        if user is None:
            return

        validation_error = None
        with transaction.atomic():
            try:
                device = self._chosen_device(user)
                token = self.cleaned_data.get("otp_token")

                user.otp_device = None

                try:
                    if self.cleaned_data.get("otp_challenge"):
                        self._handle_challenge(device)
                    elif token:
                        user.otp_device = self._verify_token(user, token, device)
                    else:
                        raise forms.ValidationError(
                            self.otp_error_messages["token_required"],
                            code="token_required",
                        )
                finally:
                    if user.otp_device is None:
                        self._update_form(user)
            except forms.ValidationError as e:
                # Validation errors shouldn't abort the transaction, so we have
                # to carefully transport them out.
                validation_error = e

        if validation_error:
            raise validation_error

    def _chosen_device(self, user):
        device_id = self.cleaned_data.get("otp_device")

        if device_id:
            device = Device.from_persistent_id(device_id, for_verify=True)
        else:
            device = None

        # SECURITY: The form doesn't validate otp_device for us, since we don't
        # have the list of choices until we authenticate the user. Without the
        # following, an attacker could authenticate using some other user's OTP
        # device.
        if (device is not None) and (device.user_id != user.pk):
            device = None

        return device

    def _handle_challenge(self, device):
        try:
            challenge = device.generate_challenge() if (device is not None) else None
        except Exception as e:
            raise forms.ValidationError(
                self.otp_error_messages["challenge_exception"].format(e),
                code="challenge_exception",
            )
        else:
            if challenge is None:
                raise forms.ValidationError(
                    self.otp_error_messages["not_interactive"], code="not_interactive"
                )
            else:
                raise forms.ValidationError(
                    self.otp_error_messages["challenge_message"].format(challenge),
                    code="challenge_message",
                )

    def _verify_token(self, user, token, device=None):
        if device is not None:
            verify_is_allowed, extra = device.verify_is_allowed()
            if not verify_is_allowed:
                # Try to match specific conditions we know about.
                if "reason" in extra and extra["reason"] == VerifyNotAllowed.N_FAILED_ATTEMPTS:
                    raise forms.ValidationError(
                        self.otp_error_messages["n_failed_attempts"] % extra
                    )
                if "error_message" in extra:
                    raise forms.ValidationError(extra["error_message"])
                # Fallback to generic message otherwise.
                raise forms.ValidationError(self.otp_error_messages["verification_not_allowed"])

            device = device if device.verify_token(token) else None
        else:
            device = match_token(user, token)

        if device is None:
            raise forms.ValidationError(
                self.otp_error_messages["invalid_token"], code="invalid_token"
            )

        return device

    def _update_form(self, user):
        if "otp_device" in self.fields:
            self.fields["otp_device"].widget.choices = self.device_choices(user)

        if "password" in self.fields:
            self.fields["password"].widget.render_value = True

    @staticmethod
    def device_choices(user):
        return list((d.persistent_id, d.name) for d in devices_for_user(user))


class OTPAuthenticationForm(OTPAuthenticationFormMixin, AuthenticationForm):
    """
    This form provides the one-stop OTP authentication solution. It should
    only be used when two-factor authentication is required: it does not
    have an OTP-optional mode. The form has four fields:

        #. ``username`` is inherited from
           :class:`~django.contrib.auth.forms.AuthenticationForm`.
        #. ``password`` is inherited from
           :class:`~django.contrib.auth.forms.AuthenticationForm`.
        #. ``otp_device`` uses a :class:`~django.forms.Select` to allow the user
           to choose one of their registered devices. It will be empty as long
           as ``form.get_user()`` is ``None`` and should generally be omitted
           from the template in that case.
        #. ``otp_token`` is the field for entering an OTP token. It should
           always be included.

    In addition, if ``form.get_user()`` is not ``None``, the template should
    include an additional submit button named ``otp_challenge``. Pressing this
    button when ``otp_device`` is set to an interactive device will cause us to
    generate a challenge value for the user. Pressing the challenge button with
    a non-interactive device selected has no effect.

    The intended behavior of the form is as follows:

        - Initially the ``username``, ``password``, and ``otp_token`` fields
          should be visible. Validation of ``username`` and ``password`` is the
          same as for :class:`~django.contrib.auth.forms.AuthenticationForm`.
          If we are able to authenticate the user based on username and password,
          then one of two things happens:

            - If the user submitted an OTP token, we will enumerate all of the
              user's OTP devices, asking each one to verify it in turn. If one
              of them succeeds, then authentication is fully successful and the
              user is logged in.

            - If the user did not submit an OTP token or none of user's devices
              accepted it, then a
              :exc:`~django.core.exceptions.ValidationError` is raised.

        - In either case, as long as the user is authenticated by their
          password, ``form.get_user()`` will return the authenticated
          :class:`~django.contrib.auth.models.User` object. From here on, this
          documentation assumes that username/password authentication succeeds
          on all subsequent submissions. If validation was not successful, then
          the form will be displayed again and this time the template should be
          sure to include the (now populated) ``otp_device`` field as well as
          the ``otp_challenge`` submit button.

        - The user will then have to choose a specific device to authenticate
          against (or accept the default). If they press the ``otp_challenge``
          button, we will ask that device to generate a challenge. The device
          will return a message for the user, which will be incorporated into
          the :exc:`~django.core.exceptions.ValidationError` message.

        - If the user presses any other submit button, we will authenticate the
          username and password as always and then verify the OTP token against
          the chosen device. When that succeeds, authentication and
          verification are successful and the user is logged in.

    Error messages can be customized in subclasses; see
    :class:`OTPAuthenticationFormMixin`.

    """

    otp_device = forms.CharField(required=False, widget=forms.Select)
    otp_token = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"autocomplete": "off"})
    )

    # This is a placeholder field that allows us to detect when the user clicks
    # the otp_challenge submit button.
    otp_challenge = forms.CharField(required=False)

    def clean(self):
        self.cleaned_data = super().clean()
        self.clean_otp(self.get_user())

        return self.cleaned_data


class OTPTokenForm(OTPAuthenticationFormMixin, forms.Form):
    """
    A form that verifies an authenticated user. It looks very much like
    :class:`~django_otp.forms.OTPAuthenticationForm`, but without the username
    and password. The first argument must be an authenticated user; for an
    example of using this in a login view, see the source for
    :class:`django_otp.views.LoginView`.

    This form will ask the user to choose one of their registered devices and
    enter an OTP token. Validation will succeed if the token is verified. See
    :class:`~django_otp.forms.OTPAuthenticationForm` for details on writing a
    compatible template (leaving out the username and password, of course).

    Error messages can be customized in subclasses; see
    :class:`OTPAuthenticationFormMixin`.

    :param user: An authenticated user.
    :type user: :class:`~django.contrib.auth.models.User`

    :param request: The current request.
    :type request: :class:`~django.http.HttpRequest`

    """

    otp_device = forms.ChoiceField(choices=[])
    otp_token = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"autocomplete": "off"})
    )
    otp_challenge = forms.CharField(required=False)

    def __init__(self, user, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user
        self.fields["otp_device"].choices = self.device_choices(user)

    def clean(self):
        super().clean()

        self.clean_otp(self.user)

        return self.cleaned_data

    def get_user(self):
        return self.user
