"""passbook access helper classes"""
from logging import getLogger

from django.contrib import messages
from django.utils.translation import gettext as _

from passbook.core.models import Application

LOGGER = getLogger(__name__)

class AccessMixin:
    """Mixin class for usage in Authorization views.
    Provider functions to check application access, etc"""

    # request is set by view but since this Mixin has no base class
    request = None

    def provider_to_application(self, provider):
        """Lookup application assigned to provider, throw error if no application assigned"""
        try:
            return provider.application
        except Application.DoesNotExist as exc:
            messages.error(self.request, _('Provider "%(name)s" has no application assigned' % {
                'name': provider
                }))
            raise exc

    def user_has_access(self, application, user):
        """Check if user has access to application."""
        LOGGER.debug("Checking permissions of %s on application %s...", user, application)
        return application.user_is_authorized(user)
