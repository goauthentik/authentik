"""Core OAauth Views"""
from typing import Callable, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import RedirectView, View
from structlog import get_logger

from passbook.audit.models import Event, EventAction
from passbook.channels.in_oauth.clients import get_client
from passbook.channels.in_oauth.models import OAuthInlet, UserOAuthInletConnection
from passbook.flows.models import Flow, FlowDesignation
from passbook.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.urls import redirect_with_qs
from passbook.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND

LOGGER = get_logger()


# pylint: disable=too-few-public-methods
class OAuthClientMixin:
    "Mixin for getting OAuth client for a inlet."

    client_class: Optional[Callable] = None

    def get_client(self, inlet):
        "Get instance of the OAuth client for this inlet."
        if self.client_class is not None:
            # pylint: disable=not-callable
            return self.client_class(inlet)
        return get_client(inlet)


class OAuthRedirect(OAuthClientMixin, RedirectView):
    "Redirect user to OAuth inlet to enable access."

    permanent = False
    params = None

    # pylint: disable=unused-argument
    def get_additional_parameters(self, inlet):
        "Return additional redirect parameters for this inlet."
        return self.params or {}

    def get_callback_url(self, inlet):
        "Return the callback url for this inlet."
        return reverse(
            "passbook_channels_in_oauth:oauth-client-callback",
            kwargs={"inlet_slug": inlet.slug},
        )

    def get_redirect_url(self, **kwargs):
        "Build redirect url for a given inlet."
        slug = kwargs.get("inlet_slug", "")
        try:
            inlet = OAuthInlet.objects.get(slug=slug)
        except OAuthInlet.DoesNotExist:
            raise Http404("Unknown OAuth inlet '%s'." % slug)
        else:
            if not inlet.enabled:
                raise Http404("inlet %s is not enabled." % slug)
            client = self.get_client(inlet)
            callback = self.get_callback_url(inlet)
            params = self.get_additional_parameters(inlet)
            return client.get_redirect_url(
                self.request, callback=callback, parameters=params
            )


class OAuthCallback(OAuthClientMixin, View):
    "Base OAuth callback view."

    inlet_id = None
    inlet = None

    def get(self, request, *_, **kwargs):
        """View Get handler"""
        slug = kwargs.get("inlet_slug", "")
        try:
            self.inlet = OAuthInlet.objects.get(slug=slug)
        except OAuthInlet.DoesNotExist:
            raise Http404("Unknown OAuth inlet '%s'." % slug)
        else:
            if not self.inlet.enabled:
                raise Http404("inlet %s is not enabled." % slug)
            client = self.get_client(self.inlet)
            callback = self.get_callback_url(self.inlet)
            # Fetch access token
            token = client.get_access_token(self.request, callback=callback)
            if token is None:
                return self.handle_login_failure(
                    self.inlet, "Could not retrieve token."
                )
            if "error" in token:
                return self.handle_login_failure(self.inlet, token["error"])
            # Fetch profile info
            info = client.get_profile_info(token)
            if info is None:
                return self.handle_login_failure(
                    self.inlet, "Could not retrieve profile."
                )
            identifier = self.get_user_id(self.inlet, info)
            if identifier is None:
                return self.handle_login_failure(self.inlet, "Could not determine id.")
            # Get or create access record
            defaults = {
                "access_token": token.get("access_token"),
            }
            existing = UserOAuthInletConnection.objects.filter(
                inlet=self.inlet, identifier=identifier
            )

            if existing.exists():
                connection = existing.first()
                connection.access_token = token.get("access_token")
                UserOAuthInletConnection.objects.filter(pk=connection.pk).update(
                    **defaults
                )
            else:
                connection = UserOAuthInletConnection(
                    inlet=self.inlet,
                    identifier=identifier,
                    access_token=token.get("access_token"),
                )
            user = authenticate(
                inlet=self.inlet, identifier=identifier, request=request
            )
            if user is None:
                LOGGER.debug("Handling new user", inlet=self.inlet)
                return self.handle_new_user(self.inlet, connection, info)
            LOGGER.debug("Handling existing user", inlet=self.inlet)
            return self.handle_existing_user(self.inlet, user, connection, info)

    # pylint: disable=unused-argument
    def get_callback_url(self, inlet):
        "Return callback url if different than the current url."
        return False

    # pylint: disable=unused-argument
    def get_error_redirect(self, inlet, reason):
        "Return url to redirect on login failure."
        return settings.LOGIN_URL

    def get_or_create_user(self, inlet, access, info):
        "Create a shell auth.User."
        raise NotImplementedError()

    # pylint: disable=unused-argument
    def get_user_id(self, inlet, info):
        "Return unique identifier from the profile info."
        id_key = self.inlet_id or "id"
        result = info
        try:
            for key in id_key.split("."):
                result = result[key]
            return result
        except KeyError:
            return None

    def handle_login(self, user, inlet, access):
        """Prepare Authentication Plan, redirect user FlowExecutor"""
        user = authenticate(
            inlet=access.inlet, identifier=access.identifier, request=self.request
        )
        # We run the Flow planner here so we can pass the Pending user in the context
        flow = get_object_or_404(Flow, designation=FlowDesignation.AUTHENTICATION)
        planner = FlowPlanner(flow)
        plan = planner.plan(self.request)
        plan.context[PLAN_CONTEXT_PENDING_USER] = user
        plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = user.backend
        plan.context[PLAN_CONTEXT_SSO] = True
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "passbook_flows:flow-executor", self.request.GET, flow_slug=flow.slug,
        )

    # pylint: disable=unused-argument
    def handle_existing_user(self, inlet, user, access, info):
        "Login user and redirect."
        messages.success(
            self.request,
            _(
                "Successfully authenticated with %(inlet)s!"
                % {"inlet": self.inlet.name}
            ),
        )
        return self.handle_login(user, inlet, access)

    def handle_login_failure(self, inlet, reason):
        "Message user and redirect on error."
        LOGGER.warning("Authentication Failure", reason=reason)
        messages.error(self.request, _("Authentication Failed."))
        return redirect(self.get_error_redirect(inlet, reason))

    def handle_new_user(self, inlet, access, info):
        "Create a shell auth.User and redirect."
        was_authenticated = False
        if self.request.user.is_authenticated:
            # there's already a user logged in, just link them up
            user = self.request.user
            was_authenticated = True
        else:
            user = self.get_or_create_user(inlet, access, info)
        access.user = user
        access.save()
        UserOAuthInletConnection.objects.filter(pk=access.pk).update(user=user)
        Event.new(
            EventAction.CUSTOM, message="Linked OAuth Inlet", inlet=inlet
        ).from_http(self.request)
        if was_authenticated:
            messages.success(
                self.request,
                _("Successfully linked %(inlet)s!" % {"inlet": self.inlet.name}),
            )
            return redirect(
                reverse(
                    "passbook_channels_in_oauth:oauth-client-user",
                    kwargs={"inlet_slug": self.inlet.slug},
                )
            )
        # User was not authenticated, new user has been created
        user = authenticate(
            inlet=access.inlet, identifier=access.identifier, request=self.request
        )
        messages.success(
            self.request,
            _(
                "Successfully authenticated with %(inlet)s!"
                % {"inlet": self.inlet.name}
            ),
        )
        return self.handle_login(user, inlet, access)


class DisconnectView(LoginRequiredMixin, View):
    """Delete connection with inlet"""

    inlet = None
    aas = None

    def dispatch(self, request, inlet_slug):
        self.inlet = get_object_or_404(OAuthInlet, slug=inlet_slug)
        self.aas = get_object_or_404(
            UserOAuthInletConnection, inlet=self.inlet, user=request.user
        )
        return super().dispatch(request, inlet_slug)

    def post(self, request, inlet_slug):
        """Delete connection object"""
        if "confirmdelete" in request.POST:
            # User confirmed deletion
            self.aas.delete()
            messages.success(request, _("Connection successfully deleted"))
            return redirect(
                reverse(
                    "passbook_channels_in_oauth:oauth-client-user",
                    kwargs={"inlet_slug": self.inlet.slug},
                )
            )
        return self.get(request, inlet_slug)

    # pylint: disable=unused-argument
    def get(self, request, inlet_slug):
        """Show delete form"""
        return render(
            request,
            "generic/delete.html",
            {
                "object": self.inlet,
                "delete_url": reverse(
                    "passbook_channels_in_oauth:oauth-client-disconnect",
                    kwargs={"inlet_slug": self.inlet.slug,},
                ),
            },
        )
