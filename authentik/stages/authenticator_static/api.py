"""AuthenticatorStaticStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api import StageSerializer
from authentik.stages.authenticator_static.models import AuthenticatorStaticStage


class AuthenticatorStaticStageSerializer(StageSerializer):
    """AuthenticatorStaticStage Serializer"""

    class Meta:

        model = AuthenticatorStaticStage
        fields = StageSerializer.Meta.fields + ["configure_flow", "token_count"]


class AuthenticatorStaticStageViewSet(ModelViewSet):
    """AuthenticatorStaticStage Viewset"""

    queryset = AuthenticatorStaticStage.objects.all()
    serializer_class = AuthenticatorStaticStageSerializer
