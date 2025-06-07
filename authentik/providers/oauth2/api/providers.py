"""OAuth2Provider API Views"""

from copy import copy
from re import compile
from re import error as RegexError

from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer, PropertyMappingPreviewSerializer
from authentik.core.models import Provider
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    OAuth2Provider,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.rbac.decorators import permission_required


class RedirectURISerializer(PassiveSerializer):
    """A single allowed redirect URI entry"""

    matching_mode = ChoiceField(choices=RedirectURIMatchingMode.choices)
    url = CharField()


class OAuth2ProviderSerializer(ProviderSerializer):
    """OAuth2Provider Serializer"""

    redirect_uris = RedirectURISerializer(many=True, source="_redirect_uris")

    def validate_redirect_uris(self, data: list) -> list:
        for entry in data:
            if entry.get("matching_mode") == RedirectURIMatchingMode.REGEX:
                url = entry.get("url")
                try:
                    compile(url)
                except RegexError:
                    raise ValidationError(
                        _("Invalid Regex Pattern: {url}".format(url=url))
                    ) from None
        return data

    class Meta:
        model = OAuth2Provider
        fields = ProviderSerializer.Meta.fields + [
            "authorization_flow",
            "client_type",
            "client_id",
            "client_secret",
            "access_code_validity",
            "access_token_validity",
            "refresh_token_validity",
            "include_claims_in_id_token",
            "signing_key",
            "encryption_key",
            "redirect_uris",
            "sub_mode",
            "property_mappings",
            "issuer_mode",
            "jwt_federation_sources",
            "jwt_federation_providers",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


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
        "access_token_validity",
        "refresh_token_validity",
        "include_claims_in_id_token",
        "signing_key",
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
        except Provider.application.RelatedObjectDoesNotExist:
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
        parameters=[
            OpenApiParameter(
                name="for_user",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
            )
        ],
    )
    @action(detail=True, methods=["GET"])
    def preview_user(self, request: Request, pk: int) -> Response:
        """Preview user data for provider"""
        provider: OAuth2Provider = self.get_object()
        for_user = request.user
        if "for_user" in request.query_params:
            try:
                for_user = (
                    get_objects_for_user(request.user, "authentik_core.preview_user")
                    .filter(pk=request.query_params.get("for_user"))
                    .first()
                )
                if not for_user:
                    raise ValidationError({"for_user": "User not found"})
            except ValueError:
                raise ValidationError({"for_user": "input must be numerical"}) from None

        scope_names = ScopeMapping.objects.filter(provider=provider).values_list(
            "scope_name", flat=True
        )
        new_request = copy(request._request)
        new_request.user = for_user
        temp_token = IDToken.new(
            provider,
            AccessToken(
                user=for_user,
                provider=provider,
                _scope=" ".join(scope_names),
                auth_time=timezone.now(),
            ),
            new_request,
        )
        serializer = PropertyMappingPreviewSerializer(instance={"preview": temp_token.to_dict()})
        return Response(serializer.data)
