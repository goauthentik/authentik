"""passbook multi-factor authentication engine"""
from logging import getLogger

from django.contrib.auth import authenticate
from django.views.generic import FormView

from passbook.core.auth.factor import AuthenticationFactor
from passbook.core.auth.mfa import MultiFactorAuthenticator
from passbook.core.forms.authentication import AuthenticationBackendFactorForm
from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)


class AuthenticationBackendFactor(FormView, AuthenticationFactor):
    """Authentication factor which authenticates against django's AuthBackend"""

    form_class = AuthenticationBackendFactorForm
    template_name = 'login/factors/backend.html'

    def form_valid(self, form):
        """Authenticate against django's authentication backend"""
        uid_fields = CONFIG.y('passbook.uid_fields')
        kwargs = {
            'password': form.cleaned_data.get('password'),
        }
        for uid_field in uid_fields:
            kwargs[uid_field] = getattr(self.authenticator.pending_user, uid_field)
        user = authenticate(self.request, **kwargs)
        if user:
            # User instance returned from authenticate() has .backend property set
            self.authenticator.pending_user = user
            self.request.session[MultiFactorAuthenticator.SESSION_USER_BACKEND] = user.backend
            return self.authenticator.user_ok()
        return self.authenticator.user_invalid()
