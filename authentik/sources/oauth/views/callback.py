"""OAuth Callback Views"""
from json import JSONDecodeError
from typing import Any, Optional

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import View
from structlog.stdlib import get_logger

from authentik.core.models import Group, User
from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, Stage, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.views.base import OAuthClientMixin

LOGGER = get_logger()
PLAN_CONTEXT_GROUPS = "goauthentik.io/sources/oauth/groups"


class OAuthCallback(OAuthClientMixin, View):
    "Base OAuth callback view."

    source: OAuthSource
    token: Optional[dict] = None

    # pylint: disable=too-many-return-statements
    def dispatch(self, request: HttpRequest, *_, **kwargs) -> HttpResponse:
        """View Get handler"""
        slug = kwargs.get("source_slug", "")
        try:
            self.source = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404(f"Unknown OAuth source '{slug}'.")

        if not self.source.enabled:
            raise Http404(f"Source {slug} is not enabled.")
        client = self.get_client(self.source, callback=self.get_callback_url(self.source))
        # Fetch access token
        self.token = client.get_access_token()
        if self.token is None:
            return self.handle_login_failure("Could not retrieve token.")
        if "error" in self.token:
            return self.handle_login_failure(self.token["error"])
        # Fetch profile info
        try:
            raw_info = client.get_profile_info(self.token)
            if raw_info is None:
                return self.handle_login_failure("Could not retrieve profile.")
        except JSONDecodeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message="Failed to JSON-decode profile.",
                raw_profile=exc.doc,
            ).from_http(self.request)
            return self.handle_login_failure("Could not retrieve profile.")
        identifier = self.get_user_id(raw_info)
        if identifier is None:
            return self.handle_login_failure("Could not determine id.")
        # Get or create access record
        enroll_info = self.get_user_enroll_context(raw_info)
        group_info = self.get_user_group_names(raw_info)
        sfm = OAuthSourceFlowManager(
            source=self.source,
            request=self.request,
            identifier=identifier,
            enroll_info=enroll_info,
        )
        sfm.policy_context = {
            "oauth_userinfo": raw_info,
            PLAN_CONTEXT_GROUPS: group_info,
        }
        return sfm.get_flow(
            access_token=self.token.get("access_token"),
        )

    def get_callback_url(self, source: OAuthSource) -> str:
        "Return callback url if different than the current url."
        return ""

    def get_error_redirect(self, source: OAuthSource, reason: str) -> str:
        "Return url to redirect on login failure."
        return settings.LOGIN_URL

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a dict of User data"""
        raise NotImplementedError()

    def get_user_group_names(self, info: dict[str, Any]) -> list[str]:
        """Return a list of all groups the user is member of"""
        return []

    def get_user_id(self, info: dict[str, Any]) -> Optional[str]:
        """Return unique identifier from the profile info."""
        if "id" in info:
            return info["id"]
        return None

    def handle_login_failure(self, reason: str) -> HttpResponse:
        "Message user and redirect on error."
        LOGGER.warning("Authentication Failure", reason=reason)
        messages.error(
            self.request,
            _(
                "Authentication failed: %(reason)s"
                % {
                    "reason": reason,
                }
            ),
        )
        return redirect(self.get_error_redirect(self.source, reason))


class OAuthSourceFlowManager(SourceFlowManager):
    """Flow manager for oauth sources"""

    connection_type = UserOAuthSourceConnection

    def get_stages_to_append(self, flow: Flow) -> list[Stage]:
        return super().get_stages_to_append(flow) + [
            # Always run this stage after the default `PostUserEnrollmentStage` stage
            # as it relies on the user object existing
            in_memory_stage(OAuthUserUpdateStage),
        ]

    def update_connection(
        self,
        connection: UserOAuthSourceConnection,
        access_token: Optional[str] = None,
    ) -> UserOAuthSourceConnection:
        """Set the access_token on the connection"""
        connection.access_token = access_token
        return connection


class OAuthUserUpdateStage(StageView):
    """Dynamically injected stage which updates the user after enrollment/authentication."""

    def handle_groups(self):
        """Sync users' groups from oauth data"""
        user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        group_names: list[str] = self.executor.plan.context[PLAN_CONTEXT_GROUPS]
        for group_name in group_names:
            Group.objects.update_or_create(name=group_name, defaults={})
        user.ak_groups.set(Group.objects.filter(name__in=[group_names]))

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Stage used after the user has been enrolled"""
        self.handle_groups()
        return self.executor.stage_ok()

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
