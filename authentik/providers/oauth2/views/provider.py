"""authentik OAuth2 OpenID well-known views"""
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, reverse
from django.views import View
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.providers.oauth2.constants import (
    ACR_AUTHENTIK_DEFAULT,
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_CLIENT_CREDENTIALS,
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_IMPLICIT,
    GRANT_TYPE_PASSWORD,
    GRANT_TYPE_REFRESH_TOKEN,
    SCOPE_OPENID,
)
from authentik.providers.oauth2.models import OAuth2Provider, ResponseTypes, ScopeMapping
from authentik.providers.oauth2.utils import cors_allow

LOGGER = get_logger()

PLAN_CONTEXT_PARAMS = "params"
PLAN_CONTEXT_SCOPES = "scopes"


class ProviderInfoView(View):
    """OpenID-compliant Provider Info"""

    provider: OAuth2Provider

    def get_info(self, provider: OAuth2Provider) -> dict[str, Any]:
        """Get dictionary for OpenID Connect information"""
        scopes = list(
            ScopeMapping.objects.filter(provider=provider).values_list("scope_name", flat=True)
        )
        if SCOPE_OPENID not in scopes:
            scopes.append(SCOPE_OPENID)
        _, supported_alg = provider.get_jwt_key()
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
            "revocation_endpoint": self.request.build_absolute_uri(
                reverse("authentik_providers_oauth2:token-revoke")
            ),
            "device_authorization_endpoint": self.request.build_absolute_uri(
                reverse("authentik_providers_oauth2:device")
            ),
            "response_types_supported": [
                ResponseTypes.CODE,
                ResponseTypes.ID_TOKEN,
                ResponseTypes.ID_TOKEN_TOKEN,
                ResponseTypes.CODE_TOKEN,
                ResponseTypes.CODE_ID_TOKEN,
                ResponseTypes.CODE_ID_TOKEN_TOKEN,
            ],
            "jwks_uri": self.request.build_absolute_uri(
                reverse(
                    "authentik_providers_oauth2:jwks",
                    kwargs={"application_slug": provider.application.slug},
                )
            ),
            "grant_types_supported": [
                GRANT_TYPE_AUTHORIZATION_CODE,
                GRANT_TYPE_REFRESH_TOKEN,
                GRANT_TYPE_IMPLICIT,
                GRANT_TYPE_CLIENT_CREDENTIALS,
                GRANT_TYPE_PASSWORD,
                GRANT_TYPE_DEVICE_CODE,
            ],
            "id_token_signing_alg_values_supported": [supported_alg],
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
            # Because claims are dynamic and per-application, the only claims listed here
            # are ones that are always set by authentik itself on every token
            "claims_supported": [
                "sub",
                "iss",
                "aud",
                "exp",
                "iat",
                "auth_time",
                "acr",
            ],
            "claims_parameter_supported": False,
        }

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """OpenID-compliant Provider Info"""
        return JsonResponse(self.get_info(self.provider), json_dumps_params={"indent": 2})

    def dispatch(
        self, request: HttpRequest, application_slug: str, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        # Since this view only supports get, we can statically set the CORS headers
        application = get_object_or_404(Application, slug=application_slug)
        self.provider: OAuth2Provider = get_object_or_404(
            OAuth2Provider, pk=application.provider_id
        )
        response = super().dispatch(request, *args, **kwargs)
        cors_allow(request, response, *self.provider.redirect_uris.split("\n"))
        return response
