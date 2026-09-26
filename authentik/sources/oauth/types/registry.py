"""Source type manager"""

from enum import Enum
from typing import Any
from urllib.parse import urlencode

from django.http.request import HttpRequest, QueryDict
from django.templatetags.static import static
from django.urls.base import reverse
from structlog.stdlib import get_logger

from authentik.flows.challenge import Challenge, RedirectChallenge
from authentik.flows.views.executor import QS_QUERY
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod, OAuthSource, PKCEMethod
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()


class RequestKind(Enum):
    """Enum of OAuth Request types"""

    CALLBACK = "callback"
    REDIRECT = "redirect"


class SourceType:
    """Source type, allows overriding of urls and views per type"""

    callback_view = OAuthCallback
    redirect_view = OAuthRedirect
    name: str = "default"
    verbose_name: str = "Default source type"

    urls_customizable = False

    request_token_url: str | None = None
    authorization_url: str | None = None
    access_token_url: str | None = None
    profile_url: str | None = None
    oidc_well_known_url: str | None = None
    oidc_jwks_url: str | None = None
    pkce: PKCEMethod = PKCEMethod.NONE

    authorization_code_auth_method: AuthorizationCodeAuthMethod = (
        AuthorizationCodeAuthMethod.BASIC_AUTH
    )

    def icon_url(self) -> str:
        """Get Icon URL for login"""
        return static(f"authentik/sources/{self.name}.svg")

    def get_forwarded_query_parameters(
        self, source: OAuthSource, request: HttpRequest
    ) -> dict[str, str]:
        """Collect the query parameters configured in `source.forward_query_parameters`
        from the current request. When running within the flow executor, the query parameters
        of the request that started the flow (for example an OAuth2 /authorize request) are
        nested within the `query` parameter."""
        names = source.forward_query_parameter_names
        if not names:
            return {}
        nested = QueryDict(request.GET.get(QS_QUERY, ""))
        params = {}
        for name in names:
            value = request.GET.get(name, nested.get(name))
            if value is not None:
                params[name] = value
        return params

    def login_challenge(self, source: OAuthSource, request: HttpRequest) -> Challenge:
        """Allow types to return custom challenges"""
        to = reverse(
            "authentik_sources_oauth:oauth-client-login",
            kwargs={"source_slug": source.slug},
        )
        if params := self.get_forwarded_query_parameters(source, request):
            to = f"{to}?{urlencode(params)}"
        return RedirectChallenge(data={"to": to})

    def get_base_user_properties(
        self, source: OAuthSource, info: dict[str, Any], **kwargs
    ) -> dict[str, Any | dict[str, Any]]:
        """Get base user properties for enrollment/update"""
        return info

    def get_base_group_properties(
        self, source: OAuthSource, group_id: str, **kwargs
    ) -> dict[str, Any | dict[str, Any]]:
        """Get base group properties for creation/update"""
        return {
            "name": group_id,
        }


class SourceTypeRegistry:
    """Registry to hold all Source types."""

    def __init__(self) -> None:
        self.__sources: list[type[SourceType]] = []

    def register(self):
        """Class decorator to register classes inline."""

        def inner_wrapper(cls):
            self.__sources.append(cls)
            return cls

        return inner_wrapper

    def get(self):
        """Get a list of all source types"""
        return self.__sources

    def get_name_tuple(self):
        """Get list of tuples of all registered names"""
        return [(x.name, x.verbose_name) for x in self.__sources]

    def find_type(self, type_name: str) -> type[SourceType]:
        """Find type based on source"""
        found_type = None
        for src_type in self.__sources:
            if src_type.name == type_name:
                return src_type
        if not found_type:
            found_type = SourceType
            LOGGER.warning(
                "no matching type found, using default",
                wanted=type_name,
                have=[x.name for x in self.__sources],
            )
        return found_type

    def find(self, type_name: str, kind: RequestKind) -> type[OAuthCallback | OAuthRedirect]:
        """Find fitting Source Type"""
        found_type = self.find_type(type_name)
        if kind == RequestKind.CALLBACK:
            return found_type.callback_view
        if kind == RequestKind.REDIRECT:
            return found_type.redirect_view
        raise ValueError


registry = SourceTypeRegistry()
