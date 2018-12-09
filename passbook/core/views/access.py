"""passbook access helper classes"""
from logging import getLogger

from django.http import Http404

from passbook.core.models import Application

LOGGER = getLogger(__name__)

class AccessMixin:
    """Mixin class for usage in Authorization views.
    Provider functions to check application access, etc"""

    def provider_to_application(self, provider):
        """Lookup application assigned to provider, throw error if no application assigned"""
        try:
            return provider.application
        except Application.DoesNotExist as exc:
            # TODO: Log that no provider has no application assigned
            LOGGER.warning('Provider "%s" has no application assigned...', provider)
            raise Http404 from exc

    def user_has_access(self, application, user):
        """Check if user has access to application."""
        LOGGER.debug("Checking permissions of %s on application %s...", user, application)
        return application.user_is_authorized(user)
