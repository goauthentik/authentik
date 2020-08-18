"""passbook OAuth2 OpenID well-known views"""
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, reverse
from django.views import View
from structlog import get_logger

from passbook.core.models import Application
from passbook.providers.oauth2.models import OAuth2Provider

LOGGER = get_logger()

PLAN_CONTEXT_PARAMS = "params"
PLAN_CONTEXT_SCOPES = "scopes"


class ProviderInfoView(View):
    """OpenID-compliant Provider Info"""

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
            {
                "issuer": provider.get_issuer(request),
                "authorization_endpoint": request.build_absolute_uri(
                    reverse("passbook_providers_oauth2:authorize")
                ),
                "token_endpoint": request.build_absolute_uri(
                    reverse("passbook_providers_oauth2:token")
                ),
                "userinfo_endpoint": request.build_absolute_uri(
                    reverse("passbook_providers_oauth2:userinfo")
                ),
                "end_session_endpoint": request.build_absolute_uri(
                    reverse("passbook_providers_oauth2:end-session")
                ),
                "introspection_endpoint": request.build_absolute_uri(
                    reverse("passbook_providers_oauth2:token-introspection")
                ),
                "response_types_supported": [provider.response_type],
                "jwks_uri": request.build_absolute_uri(
                    reverse(
                        "passbook_providers_oauth2:jwks",
                        kwargs={"application_slug": application.slug},
                    )
                ),
                "id_token_signing_alg_values_supported": [provider.jwt_alg],
                # See: http://openid.net/specs/openid-connect-core-1_0.html#SubjectIDTypes
                "subject_types_supported": ["public"],
                "token_endpoint_auth_methods_supported": [
                    "client_secret_post",
                    "client_secret_basic",
                ],
            }
        )
        response["Access-Control-Allow-Origin"] = "*"

        return response
