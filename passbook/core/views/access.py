"""passbook access helper classes"""
from typing import List, Tuple

from django.contrib import messages
from django.http import HttpRequest
from django.utils.translation import gettext as _
from structlog import get_logger

from passbook.core.models import Application, Provider, User
from passbook.policies.engine import PolicyEngine

LOGGER = get_logger()


class AccessMixin:
    """Mixin class for usage in Authorization views.
    Provider functions to check application access, etc"""

    # request is set by view but since this Mixin has no base class
    request: HttpRequest = None

    def provider_to_application(self, provider: Provider) -> Application:
        """Lookup application assigned to provider, throw error if no application assigned"""
        try:
            return provider.application
        except Application.DoesNotExist as exc:
            messages.error(
                self.request,
                _(
                    'Provider "%(name)s" has no application assigned'
                    % {"name": provider}
                ),
            )
            raise exc

    def user_has_access(
        self, application: Application, user: User
    ) -> Tuple[bool, List[str]]:
        """Check if user has access to application."""
        LOGGER.debug("Checking permissions", user=user, application=application)
        policy_engine = PolicyEngine(application.policies.all(), user, self.request)
        policy_engine.build()
        return policy_engine.result
