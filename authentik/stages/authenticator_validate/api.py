"""AuthenticatorValidateStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage


class AuthenticatorValidateStageSerializer(StageSerializer):
    """AuthenticatorValidateStage Serializer"""

    class Meta:

        model = AuthenticatorValidateStage
        fields = StageSerializer.Meta.fields + [
            "not_configured_action",
            "device_classes",
        ]


class AuthenticatorValidateStageViewSet(ModelViewSet):
    """AuthenticatorValidateStage Viewset"""

    queryset = AuthenticatorValidateStage.objects.all()
    serializer_class = AuthenticatorValidateStageSerializer
