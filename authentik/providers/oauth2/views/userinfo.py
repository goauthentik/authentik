"""authentik OAuth2 OpenID Userinfo views"""
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from structlog.stdlib import get_logger

from authentik.providers.oauth2.constants import (
    SCOPE_GITHUB_ORG_READ,
    SCOPE_GITHUB_USER,
    SCOPE_GITHUB_USER_EMAIL,
    SCOPE_GITHUB_USER_READ,
)
from authentik.providers.oauth2.models import RefreshToken, ScopeMapping
from authentik.providers.oauth2.utils import TokenResponse, cors_allow_any

LOGGER = get_logger()


class UserInfoView(View):
    """Create a dictionary with all the requested claims about the End-User.
    See: http://openid.net/specs/openid-connect-core-1_0.html#UserInfoResponse"""

    def get_scope_descriptions(self, scopes: list[str]) -> list[dict[str, str]]:
        """Get a list of all Scopes's descriptions"""
        scope_descriptions = []
        for scope in ScopeMapping.objects.filter(scope_name__in=scopes).order_by(
            "scope_name"
        ):
            if scope.description != "":
                scope_descriptions.append(
                    {"id": scope.scope_name, "name": scope.description}
                )
        # GitHub Compatibility Scopes are handeled differently, since they required custom paths
        # Hence they don't exist as Scope objects
        github_scope_map = {
            SCOPE_GITHUB_USER: _("GitHub Compatibility: Access your User Information"),
            SCOPE_GITHUB_USER_READ: _(
                "GitHub Compatibility: Access your User Information"
            ),
            SCOPE_GITHUB_USER_EMAIL: _(
                "GitHub Compatibility: Access you Email addresses"
            ),
            SCOPE_GITHUB_ORG_READ: _("GitHub Compatibility: Access your Groups"),
        }
        for scope in scopes:
            if scope in github_scope_map:
                scope_descriptions.append(
                    {"id": scope, "name": github_scope_map[scope]}
                )
        return scope_descriptions

    def get_claims(self, token: RefreshToken) -> dict[str, Any]:
        """Get a dictionary of claims from scopes that the token
        requires and are assigned to the provider."""

        scopes_from_client = token.scope
        final_claims = {}
        for scope in ScopeMapping.objects.filter(
            provider=token.provider, scope_name__in=scopes_from_client
        ).order_by("scope_name"):
            value = scope.evaluate(
                user=token.user,
                request=self.request,
                provider=token.provider,
                token=token,
            )
            if value is None:
                continue
            if not isinstance(value, dict):
                LOGGER.warning(
                    "Scope returned a non-dict value, ignoring",
                    scope=scope,
                    value=value,
                )
                continue
            LOGGER.debug("updated scope", scope=scope)
            final_claims.update(value)
        return final_claims

    def options(self, request: HttpRequest) -> HttpResponse:
        return cors_allow_any(self.request, TokenResponse({}))

    def get(self, request: HttpRequest, **kwargs) -> HttpResponse:
        """Handle GET Requests for UserInfo"""
        token: RefreshToken = kwargs["token"]
        claims = self.get_claims(token)
        claims["sub"] = token.id_token.sub
        response = TokenResponse(claims)
        cors_allow_any(self.request, response)
        return response

    def post(self, request: HttpRequest, **kwargs) -> HttpResponse:
        """POST Requests behave the same as GET Requests, so the get handler is called here"""
        return self.get(request, **kwargs)
