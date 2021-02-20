"""AuthenticatorTOTPStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_totp.models import AuthenticatorTOTPStage


class AuthenticatorTOTPStageSerializer(StageSerializer):
    """AuthenticatorTOTPStage Serializer"""

    class Meta:

        model = AuthenticatorTOTPStage
        fields = StageSerializer.Meta.fields + ["configure_flow", "digits"]


class AuthenticatorTOTPStageViewSet(ModelViewSet):
    """AuthenticatorTOTPStage Viewset"""

    queryset = AuthenticatorTOTPStage.objects.all()
    serializer_class = AuthenticatorTOTPStageSerializer
