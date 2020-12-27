"""OAuth Source Serializer"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.admin.forms.source import SOURCE_SERIALIZER_FIELDS
from authentik.core.api.utils import MetaNameSerializer
from authentik.sources.oauth.models import OAuthSource


class OAuthSourceSerializer(ModelSerializer, MetaNameSerializer):
    """OAuth Source Serializer"""

    class Meta:
        model = OAuthSource
        fields = SOURCE_SERIALIZER_FIELDS + [
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
