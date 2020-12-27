"""authentik OAuth2 OpenID well-known views"""
from typing import Any, Dict

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, reverse
from django.views import View
from structlog import get_logger

from authentik.core.models import Application
from authentik.providers.oauth2.constants import (
    ACR_AUTHENTIK_DEFAULT,
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
    SCOPE_OPENID,
)
from authentik.providers.oauth2.models import GrantTypes, OAuth2Provider, ScopeMapping

LOGGER = get_logger()

PLAN_CONTEXT_PARAMS = "params"
PLAN_CONTEXT_SCOPES = "scopes"


class ProviderInfoView(View):
    """OpenID-compliant Provider Info"""

    def get_info(self, provider: OAuth2Provider) -> Dict[str, Any]:
        """Get dictionary for OpenID Connect information"""
        scopes = list(
            ScopeMapping.objects.filter(provider=provider).values_list(
                "scope_name", flat=True
            )
        )
        if SCOPE_OPENID not in scopes:
            scopes.append(SCOPE_OPENID)
        return {
            "issuer": provider.get_issuer(self.request),
            "authorization_endpoint": self.request.build_absolute_uri(
                reverse("authentik_providers_oauth2:authorize")
            ),
            "token_endpoint": self.request.build_absolute_uri(
                reverse("authentik_providers_oauth2:token")
            ),
            "userinfo_endpoint": self.request.build_absolute_uri(
                reverse("authentik_providers_oauth2:userinfo")
            ),
            "end_session_endpoint": self.request.build_absolute_uri(
                reverse(
                    "authentik_providers_oauth2:end-session",
                    kwargs={"application_slug": provider.application.slug},
                )
            ),
            "introspection_endpoint": self.request.build_absolute_uri(
                reverse("authentik_providers_oauth2:token-introspection")
            ),
            "response_types_supported": [provider.response_type],
            "jwks_uri": self.request.build_absolute_uri(
                reverse(
                    "authentik_providers_oauth2:jwks",
                    kwargs={"application_slug": provider.application.slug},
                )
            ),
            "grant_types_supported": [
                GRANT_TYPE_AUTHORIZATION_CODE,
                GRANT_TYPE_REFRESH_TOKEN,
                GrantTypes.IMPLICIT,
            ],
            "id_token_signing_alg_values_supported": [provider.jwt_alg],
            # See: http://openid.net/specs/openid-connect-core-1_0.html#SubjectIDTypes
            "subject_types_supported": ["public"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_post",
                "client_secret_basic",
            ],
            "acr_values_supported": [ACR_AUTHENTIK_DEFAULT],
            "scopes_supported": scopes,
            # https://openid.net/specs/openid-connect-core-1_0.html#RequestObject
            "request_parameter_supported": False,
            # Because claims are dynamic and per-application, the only fixed Claim is "sub"
            "claims_supported": ["sub"],
            "claims_parameter_supported": False,
        }

    # pylint: disable=unused-argument
    def get(
        self, request: HttpRequest, application_slug: str, *args, **kwargs
    ) -> HttpResponse:
        """OpenID-compliant Provider Info"""

        application = get_object_or_404(Application, slug=application_slug)
        provider: OAuth2Provider = get_object_or_404(
            OAuth2Provider, pk=application.provider_id
        )
        response = JsonResponse(
            self.get_info(provider), json_dumps_params={"indent": 2}
        )
        response["Access-Control-Allow-Origin"] = "*"

        return response
