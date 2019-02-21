"""passbook multi-factor authentication engine"""
from logging import getLogger

from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)


class AuthenticationFactor(TemplateView):
    """Abstract Authentication factor, inherits TemplateView but can be combined with FormView"""

    form = None
    required = True
    authenticator = None
    pending_user = None
    request = None
    template_name = 'login/factors/base.html'

    def __init__(self, authenticator):
        self.authenticator = authenticator

    def get_context_data(self, **kwargs):
        kwargs['config'] = CONFIG.get('passbook')
        kwargs['is_login'] = True
        kwargs['title'] = _('Log in to your account')
        kwargs['primary_action'] = _('Log in')
        kwargs['pending_user'] = self.pending_user
        return super().get_context_data(**kwargs)
