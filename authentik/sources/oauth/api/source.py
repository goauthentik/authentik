"""OAuth Source Serializer"""
from django.urls.base import reverse_lazy
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.manager import MANAGER


class OAuthSourceSerializer(SourceSerializer):
    """OAuth Source Serializer"""

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
        ]
        extra_kwargs = {"consumer_secret": {"write_only": True}}


class OAuthSourceProviderType(PassiveSerializer):
    """OAuth Provider"""

    name = CharField(required=True)
    value = CharField(required=True)


class OAuthSourceViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = OAuthSource.objects.all()
    serializer_class = OAuthSourceSerializer
    lookup_field = "slug"

    @swagger_auto_schema(responses={200: OAuthSourceProviderType(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def provider_types(self, request: Request) -> Response:
        """Get all creatable source types"""
        data = []
        for key, value in MANAGER.get_name_tuple():
            data.append(
                {
                    "name": value,
                    "value": key,
                }
            )
        return Response(OAuthSourceProviderType(data, many=True).data)
