"""OAuth2Provider API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.providers.oauth.models import OAuth2Provider


class OAuth2ProviderSerializer(ModelSerializer):
    """OAuth2Provider Serializer"""

    class Meta:

        model = OAuth2Provider
        fields = ['pk', 'name', 'redirect_uris', 'client_type',
                  'authorization_grant_type', 'client_id', 'client_secret', ]

class OAuth2ProviderViewSet(ModelViewSet):
    """OAuth2Provider Viewset"""

    queryset = OAuth2Provider.objects.all()
    serializer_class = OAuth2ProviderSerializer
