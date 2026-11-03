"""OAuth Redirect Views"""

from typing import Any

from django.http import Http404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import RedirectView
from structlog.stdlib import get_logger

from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_GET, SESSION_KEY_PLAN
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.views.base import OAuthClientMixin

LOGGER = get_logger()


class OAuthRedirect(OAuthClientMixin, RedirectView):
    "Redirect user to OAuth source to enable access."

    permanent = False
    params = None

    def get_additional_parameters(self, source: OAuthSource) -> dict[str, Any]:
        "Return additional redirect parameters for this source."
        return self.params or {}

    def get_callback_url(self, source: OAuthSource) -> str:
        "Return the callback url for this source."
        return reverse(
            "authentik_sources_oauth:oauth-client-callback",
            kwargs={"source_slug": source.slug},
        )

    def _try_login_hint_extract(self) -> dict[str, str]:
        """Check if we're running in a flow and if we have a pending user, use that
        as login_hint"""
        params = {}
        plan: FlowPlan = self.request.session.get(SESSION_KEY_PLAN, None)
        if not plan:
            return params
        if user := plan.context.get(PLAN_CONTEXT_PENDING_USER):
            params["login_hint"] = user.email
        if identifier := plan.context.get(PLAN_CONTEXT_PENDING_USER_IDENTIFIER):
            params["login_hint"] = identifier
        return params

    def _save_next_param(self):
        """When the source is linked to directly (outside of a flow), the flow executor never
        stores the `next` query parameter in the session, so the source flow manager would
        fall back to the user interface after authentication. Only relative URLs are accepted,
        as the value ends up as the plan's redirect."""
        next_param = self.request.GET.get(NEXT_ARG_NAME)
        if not next_param:
            return
        if not url_has_allowed_host_and_scheme(next_param, allowed_hosts=None):
            LOGGER.warning("Ignoring absolute next URL", next=next_param)
            return
        self.request.session[SESSION_KEY_GET] = {NEXT_ARG_NAME: next_param}

    def get_redirect_url(self, **kwargs) -> str:
        "Build redirect url for a given source."
        slug = kwargs.get("source_slug", "")
        try:
            source: OAuthSource = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404(f"Unknown OAuth source '{slug}'.") from None
        if not source.enabled:
            raise Http404(f"source {slug} is not enabled.")
        client = self.get_client(source, callback=self.get_callback_url(source))
        params = self.get_additional_parameters(source)
        params.setdefault("scope", [])
        if source.additional_scopes != "":
            if source.additional_scopes.startswith("*"):
                params["scope"] = source.additional_scopes[1:].split(" ")
            else:
                params["scope"] += source.additional_scopes.split(" ")
        params.update(self._try_login_hint_extract())
        self._save_next_param()
        return client.get_redirect_url(params)
