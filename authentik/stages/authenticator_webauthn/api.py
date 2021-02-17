"""AuthenticateWebAuthnStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api import StageSerializer
from authentik.stages.authenticator_webauthn.models import AuthenticateWebAuthnStage


class AuthenticateWebAuthnStageSerializer(StageSerializer):
    """AuthenticateWebAuthnStage Serializer"""

    class Meta:

        model = AuthenticateWebAuthnStage
        fields = StageSerializer.Meta.fields


class AuthenticateWebAuthnStageViewSet(ModelViewSet):
    """AuthenticateWebAuthnStage Viewset"""

    queryset = AuthenticateWebAuthnStage.objects.all()
    serializer_class = AuthenticateWebAuthnStageSerializer
