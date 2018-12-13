"""passbook multi-factor authentication engine"""
from logging import getLogger

from django.contrib.auth import authenticate, login
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils.translation import gettext as _
from django.views.generic import FormView, TemplateView, View

from passbook.core.forms.authentication import AuthenticationBackendFactorForm
from passbook.core.models import User
from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)


class AuthenticationFactor(TemplateView):
    """Abstract Authentication factor, inherits TemplateView but can be combined with FormView"""

    form = None
    required = True
    authenticator = None
    request = None
    template_name = 'login/form.html'

    def __init__(self, authenticator):
        self.authenticator = authenticator

    def get_context_data(self, **kwargs):
        kwargs['config'] = CONFIG.get('passbook')
        kwargs['is_login'] = True
        kwargs['title'] = _('Log in to your account')
        kwargs['primary_action'] = _('Log in')
        return super().get_context_data(**kwargs)

class AuthenticationBackendFactor(FormView, AuthenticationFactor):
    """Authentication factor which authenticates against django's AuthBackend"""

    form_class = AuthenticationBackendFactorForm

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
            return self.authenticator.user_ok()
        return self.authenticator.user_invalid()

class DummyFactor(AuthenticationFactor):
    """Dummy factor for testing with multiple factors"""

    def post(self, request):
        """Just redirect to next factor"""
        return self.authenticator.user_ok()

class MultiFactorAuthenticator(View):
    """Wizard-like Multi-factor authenticator"""

    SESSION_FACTOR = 'passbook_factor'
    SESSION_PENDING_FACTORS = 'passbook_pending_factors'
    SESSION_PENDING_USER = 'passbook_pending_user'

    pending_user = None
    pending_factors = []

    factors = [
        AuthenticationBackendFactor,
        DummyFactor
    ]

    _current_factor = None

    def dispatch(self, request, *args, **kwargs):
        # Extract pending user from session (only remember uid)
        if MultiFactorAuthenticator.SESSION_PENDING_USER in request.session:
            self.pending_user = get_object_or_404(
                User, id=self.request.session[MultiFactorAuthenticator.SESSION_PENDING_USER])
        else:
            raise Http404
        # Read and instantiate factor from session
        factor = None
        if MultiFactorAuthenticator.SESSION_FACTOR in request.session:
            factor = next(x for x in self.factors if x.__name__ ==
                          request.session[MultiFactorAuthenticator.SESSION_FACTOR])
        else:
            factor = self.factors[0]
        # Write pending factors to session
        if MultiFactorAuthenticator.SESSION_PENDING_FACTORS in request.session:
            self.pending_factors = request.session[MultiFactorAuthenticator.SESSION_PENDING_FACTORS]
        else:
            self.pending_factors = MultiFactorAuthenticator.factors.copy()
        self._current_factor = factor(self)
        self._current_factor.request = request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """pass get request to current factor"""
        return self._current_factor.get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """pass post request to current factor"""
        return self._current_factor.post(request, *args, **kwargs)

    def user_ok(self):
        """Redirect to next Factor"""
        LOGGER.debug("Factor %s passed", self._current_factor.__name__)
        next_factor = None
        if self.pending_factors:
            next_factor = self.pending_factors.pop()
            self.request.session[MultiFactorAuthenticator.SESSION_PENDING_FACTORS] = \
                self.pending_factors
            LOGGER.debug("Next Factor is %s", next_factor)
        if next_factor:
            self.request.session[MultiFactorAuthenticator.SESSION_FACTOR] = next_factor.__name__
            LOGGER.debug("Rendering next factor")
            return self.dispatch(self.request)
        # User passed all factors
        LOGGER.debug("User passed all factors, logging in")
        return self.user_passed()

    def user_passed(self):
        """User Successfully passed all factors"""
        # user = authenticate(request=self.request, )
        login(self.request, self.pending_user)
        LOGGER.debug("Logged in user %s", self.pending_user)
        return redirect(reverse('passbook_core:overview'))

    def user_invalid(self):
        """Show error message, user could not be authenticated"""
        LOGGER.debug("User invalid")
        # TODO: Redirect to error view
