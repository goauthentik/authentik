"""OAuth2Provider API Views"""
from django.urls import reverse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.utils import MetaNameSerializer
from authentik.core.models import Provider
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping


class OAuth2ProviderSerializer(ProviderSerializer):
    """OAuth2Provider Serializer"""

    class Meta:

        model = OAuth2Provider
        fields = ProviderSerializer.Meta.fields + [
            "authorization_flow",
            "client_type",
            "client_id",
            "client_secret",
            "token_validity",
            "include_claims_in_id_token",
            "jwt_alg",
            "rsa_key",
            "redirect_uris",
            "sub_mode",
            "property_mappings",
            "issuer_mode",
        ]


class OAuth2ProviderSetupURLs(Serializer):
    """OAuth2 Provider Metadata serializer"""

    issuer = ReadOnlyField()
    authorize = ReadOnlyField()
    token = ReadOnlyField()
    user_info = ReadOnlyField()
    provider_info = ReadOnlyField()
    logout = ReadOnlyField()

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class OAuth2ProviderViewSet(ModelViewSet):
    """OAuth2Provider Viewset"""

    queryset = OAuth2Provider.objects.all()
    serializer_class = OAuth2ProviderSerializer

    @swagger_auto_schema(responses={200: OAuth2ProviderSetupURLs(many=False)})
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
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            pass
        return Response(data)


class ScopeMappingSerializer(ModelSerializer, MetaNameSerializer):
    """ScopeMapping Serializer"""

    class Meta:

        model = ScopeMapping
        fields = [
            "pk",
            "name",
            "scope_name",
            "description",
            "expression",
            "verbose_name",
            "verbose_name_plural",
        ]


class ScopeMappingViewSet(ModelViewSet):
    """ScopeMapping Viewset"""

    queryset = ScopeMapping.objects.all()
    serializer_class = ScopeMappingSerializer
