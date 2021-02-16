"""AuthenticatorValidateStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage


class AuthenticatorValidateStageSerializer(ModelSerializer):
    """AuthenticatorValidateStage Serializer"""

    class Meta:

        model = AuthenticatorValidateStage
        fields = [
            "pk",
            "name",
        ]


class AuthenticatorValidateStageViewSet(ModelViewSet):
    """AuthenticatorValidateStage Viewset"""

    queryset = AuthenticatorValidateStage.objects.all()
    serializer_class = AuthenticatorValidateStageSerializer
