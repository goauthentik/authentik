"""OAuth Redirect Views"""

from typing import Any

from django.http import Http404
from django.urls import reverse
from django.views.generic import RedirectView
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.policies.types import PolicyRequest
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

    def _eval_additional_url_parameters(self, source: OAuthSource) -> dict[str, str]:
        if source.additional_url_params == "":
            return {}

        plan: FlowPlan = self.request.session.get(SESSION_KEY_PLAN, None)
        req = PolicyRequest(user=User())
        req.http_request = self.request
        if plan:
            req.context = plan.context
            if user := plan.context.get(PLAN_CONTEXT_PENDING_USER):
                req.user = user

        evaluator = BaseEvaluator()
        evaluator._context = {
            "context": req.context,
            "http_request": self.request,
            "request": req,
        }

        try:
            result = evaluator.evaluate(source.additional_url_params)
            if isinstance(result, dict):
                reserved_params = {
                    "client_id",
                    "code_challenge",
                    "code_challenge_method",
                    "oauth_callback",
                    "oauth_token",
                    "redirect_uri",
                    "response_type",
                    "scope",
                    "state",
                }
                return {k: v for k, v in result.items() if k not in reserved_params}
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed to evaluate additional_url_params", exc=exc, source=source)

        return {}

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
        params.update(self._eval_additional_url_parameters(source))
        if "login_hint" not in params:
            params.update(self._try_login_hint_extract())

        return client.get_redirect_url(params)
