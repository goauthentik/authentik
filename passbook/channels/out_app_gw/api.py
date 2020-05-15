"""ApplicationGatewayOutlet API Views"""
from oauth2_provider.generators import generate_client_id, generate_client_secret
from oidc_provider.models import Client
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.channels.out_app_gw.models import ApplicationGatewayOutlet
from passbook.channels.out_oidc.api import OpenIDOutletSerializer


class ApplicationGatewayOutletSerializer(ModelSerializer):
    """ApplicationGatewayOutlet Serializer"""

    client = OpenIDOutletSerializer()

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.client = Client.objects.create(
            client_id=generate_client_id(), client_secret=generate_client_secret()
        )
        instance.save()
        return instance

    def update(self, instance, validated_data):
        self.instance.client.name = self.instance.name
        self.instance.client.redirect_uris = [
            f"http://{self.instance.host}/oauth2/callback",
            f"https://{self.instance.host}/oauth2/callback",
        ]
        self.instance.client.scope = ["openid", "email"]
        self.instance.client.save()
        return super().update(instance, validated_data)

    class Meta:

        model = ApplicationGatewayOutlet
        fields = ["pk", "name", "internal_host", "external_host", "client"]
        read_only_fields = ["client"]


class ApplicationGatewayOutletViewSet(ModelViewSet):
    """ApplicationGatewayOutlet Viewset"""

    queryset = ApplicationGatewayOutlet.objects.all()
    serializer_class = ApplicationGatewayOutletSerializer
