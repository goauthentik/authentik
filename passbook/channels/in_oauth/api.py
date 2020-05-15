"""OAuth Inlet Serializer"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.admin.forms.inlet import INLET_SERIALIZER_FIELDS
from passbook.channels.in_oauth.models import OAuthInlet


class OAuthInletSerializer(ModelSerializer):
    """OAuth Inlet Serializer"""

    class Meta:
        model = OAuthInlet
        fields = INLET_SERIALIZER_FIELDS + [
            "inlet_type",
            "request_token_url",
            "authorization_url",
            "access_token_url",
            "profile_url",
            "consumer_key",
            "consumer_secret",
        ]


class OAuthInletViewSet(ModelViewSet):
    """Inlet Viewset"""

    queryset = OAuthInlet.objects.all()
    serializer_class = OAuthInletSerializer
