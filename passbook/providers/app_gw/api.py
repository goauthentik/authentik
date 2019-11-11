"""ApplicationGatewayProvider API Views"""
from oauth2_provider.generators import (generate_client_id,
                                        generate_client_secret)
from oidc_provider.models import Client
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.providers.app_gw.models import ApplicationGatewayProvider
from passbook.providers.oidc.api import OpenIDProviderSerializer


class ApplicationGatewayProviderSerializer(ModelSerializer):
    """ApplicationGatewayProvider Serializer"""

    client = OpenIDProviderSerializer()

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.client = Client.objects.create(
            client_id=generate_client_id(),
            client_secret=generate_client_secret())
        instance.save()
        return instance

    def update(self, instance, validated_data):
        self.instance.client.name = self.instance.name
        self.instance.client.redirect_uris = [
            f"http://{self.instance.host}/oauth2/callback",
            f"https://{self.instance.host}/oauth2/callback",
        ]
        self.instance.client.scope = ['openid', 'email']
        self.instance.client.save()
        return super().update(instance, validated_data)

    class Meta:

        model = ApplicationGatewayProvider
        fields = ['pk', 'name', 'host', 'client']
        read_only_fields = ['client']

class ApplicationGatewayProviderViewSet(ModelViewSet):
    """ApplicationGatewayProvider Viewset"""

    queryset = ApplicationGatewayProvider.objects.all()
    serializer_class = ApplicationGatewayProviderSerializer
