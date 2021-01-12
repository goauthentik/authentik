"""OAuth Callback Views"""
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import View
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_REDIRECT,
    PLAN_CONTEXT_SOURCE,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from authentik.flows.views import NEXT_ARG_NAME, SESSION_KEY_GET, SESSION_KEY_PLAN
from authentik.lib.utils.urls import redirect_with_qs
from authentik.policies.utils import delete_none_keys
from authentik.sources.oauth.auth import AuthorizedServiceBackend
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.views.base import OAuthClientMixin
from authentik.sources.oauth.views.flows import (
    PLAN_CONTEXT_SOURCES_OAUTH_ACCESS,
    PostUserEnrollmentStage,
)
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()


class OAuthCallback(OAuthClientMixin, View):
    "Base OAuth callback view."

    source_id = None
    source = None

    # pylint: disable=too-many-return-statements
    def get(self, request: HttpRequest, *_, **kwargs) -> HttpResponse:
        """View Get handler"""
        slug = kwargs.get("source_slug", "")
        try:
            self.source = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404(f"Unknown OAuth source '{slug}'.")

        if not self.source.enabled:
            raise Http404(f"Source {slug} is not enabled.")
        client = self.get_client(
            self.source, callback=self.get_callback_url(self.source)
        )
        # Fetch access token
        token = client.get_access_token()
        if token is None:
            return self.handle_login_failure(self.source, "Could not retrieve token.")
        if "error" in token:
            return self.handle_login_failure(self.source, token["error"])
        # Fetch profile info
        info = client.get_profile_info(token)
        if info is None:
            return self.handle_login_failure(self.source, "Could not retrieve profile.")
        identifier = self.get_user_id(self.source, info)
        if identifier is None:
            return self.handle_login_failure(self.source, "Could not determine id.")
        # Get or create access record
        defaults = {
            "access_token": token.get("access_token"),
        }
        existing = UserOAuthSourceConnection.objects.filter(
            source=self.source, identifier=identifier
        )

        if existing.exists():
            connection = existing.first()
            connection.access_token = token.get("access_token")
            UserOAuthSourceConnection.objects.filter(pk=connection.pk).update(
                **defaults
            )
        else:
            connection = UserOAuthSourceConnection(
                source=self.source,
                identifier=identifier,
                access_token=token.get("access_token"),
            )
        user = AuthorizedServiceBackend().authenticate(
            source=self.source, identifier=identifier, request=request
        )
        if user is None:
            if self.request.user.is_authenticated:
                LOGGER.debug("Linking existing user", source=self.source)
                return self.handle_existing_user_link(self.source, connection, info)
            LOGGER.debug("Handling enrollment of new user", source=self.source)
            return self.handle_enroll(self.source, connection, info)
        LOGGER.debug("Handling existing user", source=self.source)
        return self.handle_existing_user(self.source, user, connection, info)

    # pylint: disable=unused-argument
    def get_callback_url(self, source: OAuthSource) -> str:
        "Return callback url if different than the current url."
        return ""

    # pylint: disable=unused-argument
    def get_error_redirect(self, source: OAuthSource, reason: str) -> str:
        "Return url to redirect on login failure."
        return settings.LOGIN_URL

    def get_user_enroll_context(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a dict of User data"""
        raise NotImplementedError()

    # pylint: disable=unused-argument
    def get_user_id(
        self, source: UserOAuthSourceConnection, info: Dict[str, Any]
    ) -> Optional[str]:
        """Return unique identifier from the profile info."""
        if "id" in info:
            return info["id"]
        return None

    def handle_login_failure(self, source: OAuthSource, reason: str) -> HttpResponse:
        "Message user and redirect on error."
        LOGGER.warning("Authentication Failure", reason=reason)
        messages.error(self.request, _("Authentication Failed."))
        return redirect(self.get_error_redirect(source, reason))

    def handle_login_flow(self, flow: Flow, **kwargs) -> HttpResponse:
        """Prepare Authentication Plan, redirect user FlowExecutor"""
        # Ensure redirect is carried through when user was trying to
        # authorize application
        final_redirect = self.request.session.get(SESSION_KEY_GET, {}).get(
            NEXT_ARG_NAME, "authentik_core:shell"
        )
        kwargs.update(
            {
                # Since we authenticate the user by their token, they have no backend set
                PLAN_CONTEXT_AUTHENTICATION_BACKEND: "django.contrib.auth.backends.ModelBackend",
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_SOURCE: self.source,
                PLAN_CONTEXT_REDIRECT: final_redirect,
            }
        )
        # We run the Flow planner here so we can pass the Pending user in the context
        planner = FlowPlanner(flow)
        plan = planner.plan(self.request, kwargs)
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_flows:flow-executor-shell",
            self.request.GET,
            flow_slug=flow.slug,
        )

    # pylint: disable=unused-argument
    def handle_existing_user(
        self,
        source: OAuthSource,
        user: User,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> HttpResponse:
        "Login user and redirect."
        messages.success(
            self.request,
            _(
                "Successfully authenticated with %(source)s!"
                % {"source": self.source.name}
            ),
        )
        flow_kwargs = {PLAN_CONTEXT_PENDING_USER: user}
        return self.handle_login_flow(source.authentication_flow, **flow_kwargs)

    def handle_existing_user_link(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> HttpResponse:
        """Handler when the user was already authenticated and linked an external source
        to their account."""
        # there's already a user logged in, just link them up
        user = self.request.user
        access.user = user
        access.save()
        UserOAuthSourceConnection.objects.filter(pk=access.pk).update(user=user)
        Event.new(
            EventAction.SOURCE_LINKED, message="Linked OAuth Source", source=source
        ).from_http(self.request)
        messages.success(
            self.request,
            _("Successfully linked %(source)s!" % {"source": self.source.name}),
        )
        return redirect(
            reverse(
                "authentik_sources_oauth:oauth-client-user",
                kwargs={"source_slug": self.source.slug},
            )
        )

    def handle_enroll(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> HttpResponse:
        """User was not authenticated and previous request was not authenticated."""
        messages.success(
            self.request,
            _(
                "Successfully authenticated with %(source)s!"
                % {"source": self.source.name}
            ),
        )
        # Because we inject a stage into the planned flow, we can't use `self.handle_login_flow`
        context = {
            # Since we authenticate the user by their token, they have no backend set
            PLAN_CONTEXT_AUTHENTICATION_BACKEND: "django.contrib.auth.backends.ModelBackend",
            PLAN_CONTEXT_SSO: True,
            PLAN_CONTEXT_SOURCE: self.source,
            PLAN_CONTEXT_PROMPT: delete_none_keys(
                self.get_user_enroll_context(source, access, info)
            ),
            PLAN_CONTEXT_SOURCES_OAUTH_ACCESS: access,
        }
        # We run the Flow planner here so we can pass the Pending user in the context
        planner = FlowPlanner(source.enrollment_flow)
        plan = planner.plan(self.request, context)
        plan.append(in_memory_stage(PostUserEnrollmentStage))
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_flows:flow-executor-shell",
            self.request.GET,
            flow_slug=source.enrollment_flow.slug,
        )
