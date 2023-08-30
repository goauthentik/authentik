"""authentik OAuth2 OpenID Userinfo views"""
from typing import Any, Optional

from deepmerge import always_merger
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.events.models import Event, EventAction
from authentik.flows.challenge import PermissionDict
from authentik.providers.oauth2.constants import (
    SCOPE_AUTHENTIK_API,
    SCOPE_GITHUB_ORG_READ,
    SCOPE_GITHUB_USER,
    SCOPE_GITHUB_USER_EMAIL,
    SCOPE_GITHUB_USER_READ,
    SCOPE_OPENID,
)
from authentik.providers.oauth2.models import (
    BaseGrantModel,
    OAuth2Provider,
    RefreshToken,
    ScopeMapping,
)
from authentik.providers.oauth2.utils import TokenResponse, cors_allow, protected_resource_view

LOGGER = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(protected_resource_view([SCOPE_OPENID]), name="dispatch")
class UserInfoView(View):
    """Create a dictionary with all the requested claims about the End-User.
    See: http://openid.net/specs/openid-connect-core-1_0.html#UserInfoResponse"""

    token: Optional[RefreshToken]

    def get_scope_descriptions(
        self, scopes: list[str], provider: OAuth2Provider
    ) -> list[PermissionDict]:
        """Get a list of all Scopes's descriptions"""
        scope_descriptions = []
        for scope in ScopeMapping.objects.filter(scope_name__in=scopes, provider=provider).order_by(
            "scope_name"
        ):
            scope_descriptions.append(PermissionDict(id=scope.scope_name, name=scope.description))
        # GitHub Compatibility Scopes are handled differently, since they required custom paths
        # Hence they don't exist as Scope objects
        special_scope_map = {
            SCOPE_GITHUB_USER: _("GitHub Compatibility: Access your User Information"),
            SCOPE_GITHUB_USER_READ: _("GitHub Compatibility: Access your User Information"),
            SCOPE_GITHUB_USER_EMAIL: _("GitHub Compatibility: Access you Email addresses"),
            SCOPE_GITHUB_ORG_READ: _("GitHub Compatibility: Access your Groups"),
            SCOPE_AUTHENTIK_API: _("authentik API Access on behalf of your user"),
        }
        for scope in scopes:
            if scope in special_scope_map:
                scope_descriptions.append(
                    PermissionDict(id=scope, name=str(special_scope_map[scope]))
                )
        return scope_descriptions

    def get_claims(self, provider: OAuth2Provider, token: BaseGrantModel) -> dict[str, Any]:
        """Get a dictionary of claims from scopes that the token
        requires and are assigned to the provider."""

        scopes_from_client = token.scope
        final_claims = {}
        for scope in ScopeMapping.objects.filter(
            provider=provider, scope_name__in=scopes_from_client
        ).order_by("scope_name"):
            scope: ScopeMapping
            value = None
            try:
                value = scope.evaluate(
                    user=token.user,
                    request=self.request,
                    provider=provider,
                    token=token,
                )
            except PropertyMappingExpressionException as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping: '{scope.name}'",
                    provider=provider,
                    mapping=scope,
                ).from_http(self.request)
                LOGGER.warning("Failed to evaluate property mapping", exc=exc)
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
            always_merger.merge(final_claims, value)
        return final_claims

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.token = kwargs.get("token", None)
        response = super().dispatch(request, *args, **kwargs)
        allowed_origins = []
        if self.token:
            allowed_origins = self.token.provider.redirect_uris.split("\n")
        cors_allow(self.request, response, *allowed_origins)
        return response

    def options(self, request: HttpRequest) -> HttpResponse:
        return TokenResponse({})

    def get(self, request: HttpRequest, **kwargs) -> HttpResponse:
        """Handle GET Requests for UserInfo"""
        if not self.token:
            return HttpResponseBadRequest()
        claims = self.get_claims(self.token.provider, self.token)
        claims["sub"] = self.token.id_token.sub
        if self.token.id_token.nonce:
            claims["nonce"] = self.token.id_token.nonce
        response = TokenResponse(claims)
        return response

    def post(self, request: HttpRequest, **kwargs) -> HttpResponse:
        """POST Requests behave the same as GET Requests, so the get handler is called here"""
        return self.get(request, **kwargs)
