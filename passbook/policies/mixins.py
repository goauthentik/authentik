"""passbook access helper classes"""
from typing import Optional

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from structlog import get_logger

from passbook.core.models import Application, Provider, User
from passbook.flows.views import SESSION_KEY_APPLICATION_PRE
from passbook.policies.engine import PolicyEngine
from passbook.policies.types import PolicyResult

LOGGER = get_logger()


class BaseMixin:
    """Base Mixin class, used to annotate View Member variables"""

    request: HttpRequest


class PolicyAccessMixin(BaseMixin, AccessMixin):
    """Mixin class for usage in Authorization views.
    Provider functions to check application access, etc"""

    def handle_no_permission(self, application: Optional[Application] = None):
        if application:
            self.request.session[SESSION_KEY_APPLICATION_PRE] = application
        return redirect_to_login(
            self.request.get_full_path(),
            self.get_login_url(),
            self.get_redirect_field_name(),
        )

    def handle_no_permission_authorized(self) -> HttpResponse:
        """Function called when user has no permissions but is authorized"""
        # TODO: Remove this URL and render the view instead
        return redirect("passbook_flows:denied")

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
        self, application: Application, user: Optional[User] = None
    ) -> PolicyResult:
        """Check if user has access to application."""
        user = user or self.request.user
        policy_engine = PolicyEngine(
            application, user or self.request.user, self.request
        )
        policy_engine.build()
        result = policy_engine.result
        LOGGER.debug(
            "AccessMixin user_has_access", user=user, app=application, result=result,
        )
        if not result.passing:
            for message in result.messages:
                messages.error(self.request, _(message))
        return result
