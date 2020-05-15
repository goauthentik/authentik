"""OpenIDOutlet API Views"""
from oidc_provider.models import Client
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

# from passbook.channels.out_oidc.models import OpenIDOutlet


class OpenIDOutletSerializer(ModelSerializer):
    """OpenIDOutlet Serializer"""

    class Meta:

        model = Client
        fields = [
            "pk",
            "name",
            "client_type",
            "client_id",
            "client_secret",
            "response_types",
            "jwt_alg",
            "reuse_consent",
            "require_consent",
            "_redirect_uris",
            "_scope",
        ]


class OpenIDOutletViewSet(ModelViewSet):
    """OpenIDOutlet Viewset"""

    queryset = Client.objects.all()
    serializer_class = OpenIDOutletSerializer
