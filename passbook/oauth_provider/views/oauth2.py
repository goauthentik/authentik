"""passbook OAuth2 Views"""

from logging import getLogger

from django.http import Http404
from django.shortcuts import get_object_or_404
from oauth2_provider.views.base import AuthorizationView

from passbook.core.views.access import AccessMixin
from passbook.oauth_provider.models import OAuth2Provider

LOGGER = getLogger(__name__)


class PassbookAuthorizationView(AccessMixin, AuthorizationView):
    """Custom OAuth2 Authorization View which checks rules, etc"""

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
            # TODO: Create a general error class for access denied
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **kwargs):
        # Always set is_login to true for correct css class
        context['is_login'] = True
        return super().render_to_response(context, **kwargs)

    def form_valid(self, form):
        # User has clicked on "Authorize"
        # TODO: Create Audit log entry
        LOGGER.debug('user %s authorized %s', self.request.user, self._application)
        return super().form_valid(form)
