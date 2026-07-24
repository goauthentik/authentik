"""OAuth Callback Views"""

from datetime import timedelta
from json import JSONDecodeError
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.generic import View
from structlog.stdlib import get_logger

from authentik.core.sources.flow_manager import (
    PLAN_CONTEXT_SOURCE_MATCH_FAILURE,
    PLAN_CONTEXT_SOURCE_STAGE_RESUME_ON_MISSING_PROPERTY,
    SESSION_KEY_OVERRIDE_FLOW_TOKEN,
    SourceFlowManager,
    clear_source_flow_session,
)
from authentik.core.sources.matcher import MatchFailure, MatchFailureReason
from authentik.events.models import Event, EventAction
from authentik.flows.models import FlowToken
from authentik.flows.planner import PLAN_CONTEXT_IS_RESTORED
from authentik.sources.oauth.clients.base import BaseOAuthClient
from authentik.sources.oauth.models import (
    GroupOAuthSourceConnection,
    OAuthSource,
    UserOAuthSourceConnection,
)
from authentik.sources.oauth.views.base import OAuthClientMixin

LOGGER = get_logger()


class OAuthCallback(OAuthClientMixin, View):
    "Base OAuth callback view."

    source: OAuthSource
    token: dict[str, Any] | None = None

    def dispatch(self, request: HttpRequest, *_, **kwargs) -> HttpResponse:
        """View Get handler"""
        slug = kwargs.get("source_slug", "")
        try:
            self.source = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404(f"Unknown OAuth source '{slug}'.") from None

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
            res = self.redirect_flow_manager(client)
        except ValueError as exc:
            # if we're authenticated and not in a source stage and this new flag is enabled,
            # just continue
            if self.request.user.is_authenticated:
                pass
            return self.handle_login_failure(exc.args[0])
        return res

    def redirect_flow_manager(self, client: BaseOAuthClient) -> HttpResponse:
        try:
            raw_info = client.get_profile_info(self.token)
            if raw_info is None:
                raise ValueError("Could not retrieve profile.")
        except JSONDecodeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message="Failed to JSON-decode profile.",
                raw_profile=exc.doc,
            ).from_http(self.request)
            raise ValueError("Could not retrieve profile.") from None
        identifier = self.get_user_id(info=raw_info)
        if identifier is None:
            raise ValueError("Could not determine id.")
        sfm = OAuthSourceFlowManager(
            source=self.source,
            request=self.request,
            identifier=identifier,
            user_info={
                "info": raw_info,
                "client": client,
                "token": self.token,
            },
            policy_context={
                "oauth_userinfo": raw_info,
            },
        )
        return sfm.get_flow(
            raw_info=raw_info,
            access_token=self.token.get("access_token"),
            refresh_token=self.token.get("refresh_token"),
            expires=self.token.get("expires_in"),
        )

    def get_callback_url(self, source: OAuthSource) -> str:
        "Return callback url if different than the current url."
        return ""

    def get_error_redirect(self, source: OAuthSource, reason: str) -> str:
        "Return url to redirect on login failure."
        return settings.LOGIN_URL

    def get_user_id(self, info: dict[str, Any]) -> str | None:
        """Return unique identifier from the profile info."""
        if "id" in info:
            return str(info["id"])
        return None

    def handle_login_failure(self, reason: str) -> HttpResponse:
        "Message user and redirect on error."
        LOGGER.warning("Authentication Failure", reason=reason)
        messages.error(
            self.request,
            _(
                "Authentication failed: {reason}".format_map(
                    {
                        "reason": reason,
                    }
                )
            ),
        )
        return redirect(self.get_error_redirect(self.source, reason))


class OAuthSourceFlowManager(SourceFlowManager):
    """Flow manager for oauth sources"""

    user_connection_type = UserOAuthSourceConnection
    group_connection_type = GroupOAuthSourceConnection

    def handle_match_failure(self, failure: MatchFailure) -> HttpResponse | None:
        """Resume an opted-in Source Stage after a missing matching property."""
        if failure.reason != MatchFailureReason.MISSING_PROPERTY:
            return None
        session_token = self.request.session.get(SESSION_KEY_OVERRIDE_FLOW_TOKEN)
        token_pk = getattr(session_token, "pk", None)
        if not token_pk:
            return None
        token = FlowToken.objects.including_expired().filter(pk=token_pk).first()
        if not token:
            clear_source_flow_session(self.request)
            return None
        if token.is_expired:
            token.expire_action()
            clear_source_flow_session(self.request)
            return None
        plan = token.plan
        resume_config = plan.context.get(PLAN_CONTEXT_SOURCE_STAGE_RESUME_ON_MISSING_PROPERTY)
        current_stage = plan.bindings[0].stage if plan.bindings else None
        if (
            not isinstance(resume_config, dict)
            or resume_config.get("source") != str(self.source.pk)
            or resume_config.get("stage") != str(getattr(current_stage, "pk", None))
            or getattr(current_stage, "source_id", None) != self.source.pk
        ):
            return None

        plan.context.pop(PLAN_CONTEXT_SOURCE_STAGE_RESUME_ON_MISSING_PROPERTY, None)
        plan.context.update(self.policy_context)
        plan.context[PLAN_CONTEXT_SOURCE_MATCH_FAILURE] = {
            "reason": failure.reason.value,
            "property": failure.property,
            "source": self.source.slug,
        }
        plan.context[PLAN_CONTEXT_IS_RESTORED] = session_token
        response = plan.to_redirect(self.request, token.flow)
        token.delete()
        return response

    def update_user_connection(
        self,
        connection: UserOAuthSourceConnection,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_in: int | None = None,
        **_,
    ) -> UserOAuthSourceConnection:
        """Set the access_token and refresh_token on the connection"""
        connection.access_token = access_token
        connection.refresh_token = refresh_token
        connection.expires = now() + timedelta(seconds=expires_in) if expires_in else now()
        return connection
