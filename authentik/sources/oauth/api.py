"""OAuth Source Serializer"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.sources.oauth.models import OAuthSource


class OAuthSourceSerializer(SourceSerializer):
    """OAuth Source Serializer"""

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
        ]


class OAuthSourceViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = OAuthSource.objects.all()
    serializer_class = OAuthSourceSerializer
    lookup_field = "slug"
