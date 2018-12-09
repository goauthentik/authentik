"""Core views"""
from logging import getLogger
from typing import Dict

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, reverse
from django.utils.translation import ugettext as _
from django.views import View
from django.views.generic import FormView

from passbook.core.forms.authentication import LoginForm
from passbook.core.models import User
from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)

class LoginView(UserPassesTestMixin, FormView):
    """Allow users to sign in"""

    template_name = 'login/form.html'
    form_class = LoginForm
    success_url = '.'

    # Allow only not authenticated users to login
    def test_func(self):
        return self.request.user.is_authenticated is False

    def handle_no_permission(self):
        return self.logged_in_redirect()

    def logged_in_redirect(self):
        """User failed check so user is authenticated already.
        Either redirect to ?next param or home."""
        if 'next' in self.request.GET:
            return redirect(self.request.GET.get('next'))
        return redirect(reverse('passbook_core:overview'))

    def get_context_data(self, **kwargs):
        kwargs['config'] = CONFIG.get('passbook')
        kwargs['is_login'] = True
        return super().get_context_data(**kwargs)

    def get_user(self, uid_value) -> User:
        """Find user instance. Returns None if no user was found."""
        for search_field in CONFIG.y('passbook.uid_fields'):
            users = User.objects.filter(**{search_field: uid_value})
            if users.exists():
                return users.first()
        return None

    def form_valid(self, form: LoginForm) -> HttpResponse:
        """Form data is valid"""
        pre_user = self.get_user(form.cleaned_data.get('uid_field'))
        if not pre_user:
            # No user found
            return self.invalid_login(self.request)
        user = authenticate(
            email=pre_user.email,
            username=pre_user.username,
            password=form.cleaned_data.get('password'),
            request=self.request)
        if user:
            # User authenticated successfully
            return self.login(self.request, user, form.cleaned_data)
        # User was found but couldn't authenticate
        return self.invalid_login(self.request, disabled_user=pre_user)

    def login(self, request: HttpRequest, user: User, cleaned_data: Dict) -> HttpResponse:
        """Handle actual login

        Actually logs user in, sets session expiry and redirects to ?next parameter

        Args:
            request: The current request
            user: The user to be logged in.

        Returns:
            Either redirect to ?next or if not present to overview
        """
        if user is None:
            raise ValueError("User cannot be None")
        login(request, user)

        if cleaned_data.get('remember') is True:
            request.session.set_expiry(CONFIG.y('passbook.session.remember_age'))
        else:
            request.session.set_expiry(0)  # Expires when browser is closed
        messages.success(request, _("Successfully logged in!"))
        LOGGER.debug("Successfully logged in %s", user.username)
        return self.logged_in_redirect()

    def invalid_login(self, request: HttpRequest, disabled_user: User = None) -> HttpResponse:
        """Handle login for disabled users/invalid login attempts"""
        messages.error(request, _('Failed to authenticate.'))
        return self.render_to_response(self.get_context_data())

class LogoutView(LoginRequiredMixin, View):
    """Log current user out"""

    def dispatch(self, request):
        """Log current user out"""
        logout(request)
        messages.success(request, _("You've successfully been logged out."))
        return redirect(reverse('passbook_core:auth-login'))
