"""OAuth2Provider API Views"""
from django.urls import reverse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.api.decorators import permission_required
from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer, PropertyMappingPreviewSerializer
from authentik.core.models import Provider
from authentik.providers.oauth2.models import OAuth2Provider, RefreshToken, ScopeMapping


class OAuth2ProviderSerializer(ProviderSerializer):
    """OAuth2Provider Serializer"""

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
            "signing_key",
            "redirect_uris",
            "sub_mode",
            "property_mappings",
            "issuer_mode",
            "jwks_sources",
        ]


class OAuth2ProviderSetupURLs(PassiveSerializer):
    """OAuth2 Provider Metadata serializer"""

    issuer = CharField(read_only=True)
    authorize = CharField(read_only=True)
    token = CharField(read_only=True)
    user_info = CharField(read_only=True)
    provider_info = CharField(read_only=True)
    logout = CharField(read_only=True)
    jwks = CharField(read_only=True)


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
        "signing_key",
        "redirect_uris",
        "sub_mode",
        "property_mappings",
        "issuer_mode",
    ]
    search_fields = ["name"]
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
                    "authentik_providers_oauth2:end-session",
                    kwargs={"application_slug": provider.application.slug},
                )
            )
            data["jwks"] = request.build_absolute_uri(
                reverse(
                    "authentik_providers_oauth2:jwks",
                    kwargs={"application_slug": provider.application.slug},
                )
            )
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            pass
        return Response(data)

    @permission_required(
        "authentik_providers_oauth2.view_oauth2provider",
    )
    @extend_schema(
        responses={
            200: PropertyMappingPreviewSerializer(),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(detail=True, methods=["GET"])
    # pylint: disable=invalid-name, unused-argument
    def preview_user(self, request: Request, pk: int) -> Response:
        """Preview user data for provider"""
        provider: OAuth2Provider = self.get_object()
        temp_token = RefreshToken()
        temp_token.scope = ScopeMapping.objects.filter(provider=provider).values_list(
            "scope_name", flat=True
        )
        temp_token.provider = provider
        temp_token.user = request.user
        serializer = PropertyMappingPreviewSerializer(
            instance={"preview": temp_token.create_id_token(request.user, request).to_dict()}
        )
        return Response(serializer.data)
