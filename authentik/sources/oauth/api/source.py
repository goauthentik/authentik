"""OAuth Source Serializer"""
from django.urls.base import reverse_lazy
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_field
from requests import RequestException
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, ChoiceField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.lib.utils.http import get_http_session
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.manager import MANAGER, SourceType


class SourceTypeSerializer(PassiveSerializer):
    """Serializer for SourceType"""

    name = CharField(required=True)
    slug = CharField(required=True)
    urls_customizable = BooleanField()
    request_token_url = CharField(read_only=True, allow_null=True)
    authorization_url = CharField(read_only=True, allow_null=True)
    access_token_url = CharField(read_only=True, allow_null=True)
    profile_url = CharField(read_only=True, allow_null=True)


class OAuthSourceSerializer(SourceSerializer):
    """OAuth Source Serializer"""

    provider_type = ChoiceField(choices=MANAGER.get_name_tuple())
    callback_url = SerializerMethodField()

    def get_callback_url(self, instance: OAuthSource) -> str:
        """Get OAuth Callback URL"""
        relative_url = reverse_lazy(
            "authentik_sources_oauth:oauth-client-callback",
            kwargs={"source_slug": instance.slug},
        )
        if "request" not in self.context:
            return relative_url
        return self.context["request"].build_absolute_uri(relative_url)

    type = SerializerMethodField()

    @extend_schema_field(SourceTypeSerializer)
    def get_type(self, instance: OAuthSource) -> SourceTypeSerializer:
        """Get source's type configuration"""
        return SourceTypeSerializer(instance.type).data

    def validate(self, attrs: dict) -> dict:
        session = get_http_session()
        well_known = attrs.get("oidc_well_known_url")
        if well_known and well_known != "":
            try:
                well_known_config = session.get(well_known)
                well_known_config.raise_for_status()
            except RequestException as exc:
                raise ValidationError(exc.response.text)
            config = well_known_config.json()
            try:
                attrs["authorization_url"] = config["authorization_endpoint"]
                attrs["access_token_url"] = config["token_endpoint"]
                attrs["profile_url"] = config["userinfo_endpoint"]
                attrs["oidc_jwks_url"] = config["jwks_uri"]
            except (IndexError, KeyError) as exc:
                raise ValidationError(f"Invalid well-known configuration: {exc}")

        jwks_url = attrs.get("oidc_jwks_url")
        if jwks_url and jwks_url != "":
            try:
                jwks_config = session.get(jwks_url)
                jwks_config.raise_for_status()
            except RequestException as exc:
                raise ValidationError(exc.response.text)
            config = jwks_config.json()
            attrs["oidc_jwks"] = config

        provider_type = MANAGER.find_type(attrs.get("provider_type", ""))
        for url in [
            "authorization_url",
            "access_token_url",
            "profile_url",
        ]:
            if getattr(provider_type, url, None) is None:
                if url not in attrs:
                    raise ValidationError(f"{url} is required for provider {provider_type.name}")
        return attrs

    class Meta:
        model = OAuthSource
        fields = SourceSerializer.Meta.fields + [
            "provider_type",
            "request_token_url",
            "authorization_url",
            "access_token_url",
            "profile_url",
            "consumer_key",
            "consumer_secret",
            "callback_url",
            "additional_scopes",
            "type",
            "oidc_well_known_url",
            "oidc_jwks_url",
            "oidc_jwks",
        ]
        extra_kwargs = {"consumer_secret": {"write_only": True}}


class OAuthSourceViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = OAuthSource.objects.all()
    serializer_class = OAuthSourceSerializer
    lookup_field = "slug"
    filterset_fields = [
        "name",
        "slug",
        "enabled",
        "authentication_flow",
        "enrollment_flow",
        "policy_engine_mode",
        "user_matching_mode",
        "provider_type",
        "request_token_url",
        "authorization_url",
        "access_token_url",
        "profile_url",
        "consumer_key",
        "additional_scopes",
    ]
    search_fields = ["name", "slug"]
    ordering = ["name"]

    @extend_schema(
        responses={200: SourceTypeSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name="name",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
            )
        ],
    )
    @action(detail=False, pagination_class=None, filter_backends=[])
    def source_types(self, request: Request) -> Response:
        """Get all creatable source types. If ?name is set, only returns the type for <name>.
        If <name> isn't found, returns the default type."""
        data = []
        if "name" in request.query_params:
            source_type = MANAGER.find_type(request.query_params.get("name"))
            if source_type.__class__ != SourceType:
                data.append(SourceTypeSerializer(source_type).data)
        else:
            for source_type in MANAGER.get():
                data.append(SourceTypeSerializer(source_type).data)
        return Response(data)
