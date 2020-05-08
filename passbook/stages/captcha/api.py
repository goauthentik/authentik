"""CaptchaStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.captcha.models import CaptchaStage


class CaptchaStageSerializer(ModelSerializer):
    """CaptchaStage Serializer"""

    class Meta:

        model = CaptchaStage
        fields = ["pk", "name", "public_key", "private_key"]


class CaptchaStageViewSet(ModelViewSet):
    """CaptchaStage Viewset"""

    queryset = CaptchaStage.objects.all()
    serializer_class = CaptchaStageSerializer
