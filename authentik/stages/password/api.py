"""PasswordStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.password.models import PasswordStage


class PasswordStageSerializer(StageSerializer):
    """PasswordStage Serializer"""

    class Meta:

        model = PasswordStage
        fields = StageSerializer.Meta.fields + [
            "backends",
            "configure_flow",
            "failed_attempts_before_cancel",
        ]


class PasswordStageViewSet(ModelViewSet):
    """PasswordStage Viewset"""

    queryset = PasswordStage.objects.all()
    serializer_class = PasswordStageSerializer
