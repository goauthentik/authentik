"""passbook OAuth2 Views"""
from typing import Optional
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import Form
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils.translation import ugettext as _
from oauth2_provider.views.base import AuthorizationView
from structlog import get_logger

from passbook.audit.models import Event, EventAction
from passbook.channels.out_oauth.models import OAuth2Outlet
from passbook.core.models import Application
from passbook.core.views.access import AccessMixin
from passbook.core.views.utils import LoadingView, PermissionDeniedView

LOGGER = get_logger()


class PassbookAuthorizationLoadingView(LoginRequiredMixin, LoadingView):
    """Show loading view for permission checks"""

    title = _("Checking permissions...")

    def get_url(self):
        querystring = "?" + urlencode(self.request.GET)
        return reverse("passbook_channels_out_oauth:oauth2-ok-authorize") + querystring


class OAuthPermissionDenied(PermissionDeniedView):
    """Show permission denied view"""


class PassbookAuthorizationView(AccessMixin, AuthorizationView):
    """Custom OAuth2 Authorization View which checks policies, etc"""

    _application: Optional[Application] = None

    def _inject_response_type(self):
        """Inject response_type into querystring if not set"""
        LOGGER.debug("response_type not set, defaulting to 'code'")
        querystring = "?" + urlencode(self.request.GET)
        querystring += "&response_type=code"
        return redirect(
            reverse("passbook_channels_out_oauth:oauth2-ok-authorize") + querystring
        )

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Update OAuth2Outlet's skip_authorization state"""
        # Get client_id to get outlet, so we can update skip_authorization field
        client_id = request.GET.get("client_id")
        outlet = get_object_or_404(OAuth2Outlet, client_id=client_id)
        try:
            application = self.outlet_to_application(outlet)
        except Application.DoesNotExist:
            return redirect("passbook_channels_out_oauth:oauth2-permission-denied")
        # Update field here so oauth-toolkit does work for us
        outlet.skip_authorization = application.skip_authorization
        outlet.save()
        self._application = application
        # Check permissions
        passing, policy_messages = self.user_has_access(self._application, request.user)
        if not passing:
            for policy_message in policy_messages:
                messages.error(request, policy_message)
            return redirect("passbook_channels_out_oauth:oauth2-permission-denied")
        # Some clients don't pass response_type, so we default to code
        if "response_type" not in request.GET:
            return self._inject_response_type()
        actual_response = AuthorizationView.dispatch(self, request, *args, **kwargs)
        if actual_response.status_code == 400:
            LOGGER.debug("Bad request", redirect_uri=request.GET.get("redirect_uri"))
        return actual_response

    def form_valid(self, form: Form):
        # User has clicked on "Authorize"
        Event.new(
            EventAction.AUTHORIZE_APPLICATION, authorized_application=self._application,
        ).from_http(self.request)
        LOGGER.debug(
            "User authorized Application",
            user=self.request.user,
            application=self._application,
        )
        return AuthorizationView.form_valid(self, form)
