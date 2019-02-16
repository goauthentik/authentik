"""passbook OAuth2 Views"""
from logging import getLogger
from urllib.parse import urlencode

from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils.translation import ugettext as _
from oauth2_provider.views.base import AuthorizationView

from passbook.audit.models import AuditEntry
from passbook.core.views.access import AccessMixin
from passbook.core.views.utils import LoadingView, PermissionDeniedView
from passbook.oauth_provider.models import OAuth2Provider

LOGGER = getLogger(__name__)


class PassbookAuthorizationLoadingView(LoadingView):
    """Show loading view for permission checks"""

    title = _('Checking permissions...')

    def get_url(self):
        querystring = urlencode(self.request.GET)
        return reverse('passbook_oauth_provider:oauth2-ok-authorize')+'?'+querystring


class OAuthPermissionDenied(PermissionDeniedView):
    """Show permission denied view"""


class PassbookAuthorizationView(AccessMixin, AuthorizationView):
    """Custom OAuth2 Authorization View which checks policies, etc"""

    _application = None

    def dispatch(self, request, *args, **kwargs):
        """Update OAuth2Provider's skip_authorization state"""
        # Get client_id to get provider, so we can update skip_authorization field
        client_id = request.GET.get('client_id')
        provider = get_object_or_404(OAuth2Provider, client_id=client_id)
        application = self.provider_to_application(provider)
        # Update field here so oauth-toolkit does work for us
        provider.skip_authorization = application.skip_authorization
        provider.save()
        self._application = application
        # Check permissions
        if not self.user_has_access(self._application, request.user):
            return redirect(reverse('passbook_oauth_provider:oauth2-permission-denied'))
        actual_response = super().dispatch(request, *args, **kwargs)
        if actual_response.status_code == 400:
            LOGGER.debug(request.GET.get('redirect_uri'))
        return actual_response

    def render_to_response(self, context, **kwargs):
        # Always set is_login to true for correct css class
        context['is_login'] = True
        return super().render_to_response(context, **kwargs)

    def form_valid(self, form):
        # User has clicked on "Authorize"
        AuditEntry.create(
            action=AuditEntry.ACTION_AUTHORIZE_APPLICATION,
            request=self.request,
            app=str(self._application))
        LOGGER.debug('user %s authorized %s', self.request.user, self._application)
        return super().form_valid(form)
