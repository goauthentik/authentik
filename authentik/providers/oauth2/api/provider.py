"""OAuth2Provider API Views"""
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Provider
from authentik.providers.oauth2.models import JWTAlgorithms, OAuth2Provider


class OAuth2ProviderSerializer(ProviderSerializer):
    """OAuth2Provider Serializer"""

    def validate_jwt_alg(self, value):
        """Ensure that when RS256 is selected, a certificate-key-pair is selected"""
        if self.initial_data.get("rsa_key", None) is None and value == JWTAlgorithms.RS256:
            raise ValidationError(_("RS256 requires a Certificate-Key-Pair to be selected."))
        return value

    class Meta:

        model = OAuth2Provider
        fields = ProviderSerializer.Meta.fields + [
            "authorization_flow",
            "client_type",
            "client_id",
            "client_secret",
            "access_code_validity",
            "token_validity",
            "include_claims_in_id_token",
            "jwt_alg",
            "rsa_key",
            "redirect_uris",
            "sub_mode",
            "property_mappings",
            "issuer_mode",
        ]


class OAuth2ProviderSetupURLs(PassiveSerializer):
    """OAuth2 Provider Metadata serializer"""

    issuer = ReadOnlyField()
    authorize = ReadOnlyField()
    token = ReadOnlyField()
    user_info = ReadOnlyField()
    provider_info = ReadOnlyField()
    logout = ReadOnlyField()


class OAuth2ProviderViewSet(UsedByMixin, ModelViewSet):
    """OAuth2Provider Viewset"""

    queryset = OAuth2Provider.objects.all()
    serializer_class = OAuth2ProviderSerializer
    filterset_fields = [
        "name",
        "authorization_flow",
        "property_mappings",
        "application",
        "authorization_flow",
        "client_type",
        "client_id",
        "access_code_validity",
        "token_validity",
        "include_claims_in_id_token",
        "jwt_alg",
        "rsa_key",
        "redirect_uris",
        "sub_mode",
        "property_mappings",
        "issuer_mode",
    ]
    ordering = ["name"]

    @extend_schema(
        responses={
            200: OAuth2ProviderSetupURLs,
            404: OpenApiResponse(description="Provider has no application assigned"),
        }
    )
    @action(methods=["GET"], detail=True)
    # pylint: disable=invalid-name
    def setup_urls(self, request: Request, pk: int) -> str:
        """Get Providers setup URLs"""
        provider = get_object_or_404(OAuth2Provider, pk=pk)
        data = {
            "issuer": provider.get_issuer(request),
            "authorize": request.build_absolute_uri(
                reverse(
                    "authentik_providers_oauth2:authorize",
                )
            ),
            "token": request.build_absolute_uri(
                reverse(
                    "authentik_providers_oauth2:token",
                )
            ),
            "user_info": request.build_absolute_uri(
                reverse(
                    "authentik_providers_oauth2:userinfo",
                )
            ),
            "provider_info": None,
            "logout": None,
        }
        try:
            data["provider_info"] = request.build_absolute_uri(
                reverse(
                    "authentik_providers_oauth2:provider-info",
                    kwargs={"application_slug": provider.application.slug},
                )
            )
            data["logout"] = request.build_absolute_uri(
                reverse(
                    "authentik_core:if-session-end",
                    kwargs={"application_slug": provider.application.slug},
                )
            )
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            pass
        return Response(data)
