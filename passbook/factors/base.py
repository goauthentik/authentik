"""passbook multi-factor authentication engine"""
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from passbook.core.models import User
from passbook.factors.view import AuthenticationView
from passbook.lib.config import CONFIG


class AuthenticationFactor(TemplateView):
    """Abstract Authentication factor, inherits TemplateView but can be combined with FormView"""

    form: ModelForm = None
    required: bool = True
    authenticator: AuthenticationView
    pending_user: User
    request: HttpRequest = None
    template_name = 'login/form_with_user.html'

    def __init__(self, authenticator: AuthenticationView):
        self.authenticator = authenticator
        self.pending_user = None

    def get_context_data(self, **kwargs):
        kwargs['config'] = CONFIG.y('passbook')
        kwargs['is_login'] = True
        kwargs['title'] = _('Log in to your account')
        kwargs['primary_action'] = _('Log in')
        kwargs['user'] = self.pending_user
        return super().get_context_data(**kwargs)
