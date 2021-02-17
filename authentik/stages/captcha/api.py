"""CaptchaStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api import StageSerializer
from authentik.stages.captcha.models import CaptchaStage


class CaptchaStageSerializer(StageSerializer):
    """CaptchaStage Serializer"""

    class Meta:

        model = CaptchaStage
        fields = StageSerializer.Meta.fields + ["public_key", "private_key"]


class CaptchaStageViewSet(ModelViewSet):
    """CaptchaStage Viewset"""

    queryset = CaptchaStage.objects.all()
    serializer_class = CaptchaStageSerializer
