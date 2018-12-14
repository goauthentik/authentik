"""passbook multi-factor authentication engine"""
from logging import getLogger

from django.conf import settings
from django.contrib.auth import login
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views.generic import View

from passbook.core.models import User
from passbook.core.views.utils import PermissionDeniedView
from passbook.lib.utils.reflection import class_to_path, path_to_class

LOGGER = getLogger(__name__)

class MultiFactorAuthenticator(View):
    """Wizard-like Multi-factor authenticator"""

    SESSION_FACTOR = 'passbook_factor'
    SESSION_PENDING_FACTORS = 'passbook_pending_factors'
    SESSION_PENDING_USER = 'passbook_pending_user'
    SESSION_USER_BACKEND = 'passbook_user_backend'

    pending_user = None
    pending_factors = []

    factors = settings.AUTHENTICATION_FACTORS.copy()

    _current_factor = None

    def dispatch(self, request, *args, **kwargs):
        # Extract pending user from session (only remember uid)
        if MultiFactorAuthenticator.SESSION_PENDING_USER in request.session:
            self.pending_user = get_object_or_404(
                User, id=self.request.session[MultiFactorAuthenticator.SESSION_PENDING_USER])
        else:
            raise Http404
        # Write pending factors to session
        if MultiFactorAuthenticator.SESSION_PENDING_FACTORS in request.session:
            self.pending_factors = request.session[MultiFactorAuthenticator.SESSION_PENDING_FACTORS]
        else:
            self.pending_factors = self.factors.copy()
        # Read and instantiate factor from session
        factor_class = None
        if MultiFactorAuthenticator.SESSION_FACTOR not in request.session:
            factor_class = self.pending_factors[0]
        else:
            factor_class = request.session[MultiFactorAuthenticator.SESSION_FACTOR]
        factor = path_to_class(factor_class)
        self._current_factor = factor(self)
        self._current_factor.request = request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """pass get request to current factor"""
        LOGGER.debug("Passing GET to %s", class_to_path(self._current_factor.__class__))
        return self._current_factor.get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """pass post request to current factor"""
        LOGGER.debug("Passing POST to %s", class_to_path(self._current_factor.__class__))
        return self._current_factor.post(request, *args, **kwargs)

    def user_ok(self):
        """Redirect to next Factor"""
        LOGGER.debug("Factor %s passed", class_to_path(self._current_factor.__class__))
        # Remove passed factor from pending factors
        if class_to_path(self._current_factor.__class__) in self.pending_factors:
            self.pending_factors.remove(class_to_path(self._current_factor.__class__))
        next_factor = None
        if self.pending_factors:
            next_factor = self.pending_factors.pop()
            self.request.session[MultiFactorAuthenticator.SESSION_PENDING_FACTORS] = \
                self.pending_factors
            self.request.session[MultiFactorAuthenticator.SESSION_FACTOR] = next_factor
            LOGGER.debug("Rendering Factor is %s", next_factor)
            return redirect(reverse('passbook_core:mfa'))
        # User passed all factors
        LOGGER.debug("User passed all factors, logging in")
        return self._user_passed()

    def user_invalid(self):
        """Show error message, user could not be authenticated"""
        LOGGER.debug("User invalid")
        return redirect(reverse('passbook_core:mfa-denied'))

    def _user_passed(self):
        """User Successfully passed all factors"""
        # user = authenticate(request=self.request, )
        backend = self.request.session[MultiFactorAuthenticator.SESSION_USER_BACKEND]
        login(self.request, self.pending_user, backend=backend)
        LOGGER.debug("Logged in user %s", self.pending_user)
        return redirect(reverse('passbook_core:overview'))

class MFAPermissionDeniedView(PermissionDeniedView):
    """User could not be authenticated"""
