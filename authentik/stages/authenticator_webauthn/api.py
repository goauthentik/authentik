"""AuthenticateWebAuthnStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.stages.authenticator_webauthn.models import AuthenticateWebAuthnStage


class AuthenticateWebAuthnStageSerializer(ModelSerializer):
    """AuthenticateWebAuthnStage Serializer"""

    class Meta:

        model = AuthenticateWebAuthnStage
        fields = ["pk", "name"]


class AuthenticateWebAuthnStageViewSet(ModelViewSet):
    """AuthenticateWebAuthnStage Viewset"""

    queryset = AuthenticateWebAuthnStage.objects.all()
    serializer_class = AuthenticateWebAuthnStageSerializer
