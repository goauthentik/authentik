"""SAMLInlet API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.channels.in_saml.models import SAMLInlet


class SAMLInletSerializer(ModelSerializer):
    """SAMLInlet Serializer"""

    class Meta:

        model = SAMLInlet
        fields = [
            "pk",
            "issuer",
            "idp_url",
            "idp_logout_url",
            "auto_logout",
            "signing_kp",
        ]


class SAMLInletViewSet(ModelViewSet):
    """SAMLInlet Viewset"""

    queryset = SAMLInlet.objects.all()
    serializer_class = SAMLInletSerializer
