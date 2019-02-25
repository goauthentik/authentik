"""passbook multi-factor authentication engine"""
from logging import getLogger

from django.contrib import messages
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from django.forms.utils import ErrorList
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import FormView

from passbook.core.auth.factor import AuthenticationFactor
from passbook.core.auth.view import AuthenticationView
from passbook.core.forms.authentication import PasswordFactorForm
from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)


class PasswordFactor(FormView, AuthenticationFactor):
    """Authentication factor which authenticates against django's AuthBackend"""

    form_class = PasswordFactorForm
    template_name = 'login/factors/backend.html'

    def get_context_data(self, **kwargs):
        kwargs['show_password_forget_notice'] = CONFIG.y('passbook.password_reset.enabled')
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        if 'password-forgotten' in request.GET:
            # TODO: Save nonce key in database for password reset
            # TODO: Send email to user
            self.authenticator.cleanup()
            messages.success(request, _('Check your E-Mails for a password reset link.'))
            return redirect('passbook_core:auth-login')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """Authenticate against django's authentication backend"""
        uid_fields = CONFIG.y('passbook.uid_fields')
        kwargs = {
            'password': form.cleaned_data.get('password'),
        }
        for uid_field in uid_fields:
            kwargs[uid_field] = getattr(self.authenticator.pending_user, uid_field)
        try:
            user = authenticate(self.request, **kwargs)
            if user:
                # User instance returned from authenticate() has .backend property set
                self.authenticator.pending_user = user
                self.request.session[AuthenticationView.SESSION_USER_BACKEND] = user.backend
                return self.authenticator.user_ok()
            # No user was found -> invalid credentials
            LOGGER.debug("Invalid credentials")
            # Manually inject error into form
            # pylint: disable=protected-access
            errors = form._errors.setdefault("password", ErrorList())
            errors.append(_("Invalid password"))
            return self.form_invalid(form)
        except PermissionDenied:
            # User was found, but permission was denied (i.e. user is not active)
            LOGGER.debug("Denied access to %s", kwargs)
            return self.authenticator.user_invalid()
