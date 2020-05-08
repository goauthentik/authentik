"""OTPStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.otp.models import OTPStage


class OTPStageSerializer(ModelSerializer):
    """OTPStage Serializer"""

    class Meta:

        model = OTPStage
        fields = ["pk", "name", "enforced"]


class OTPStageViewSet(ModelViewSet):
    """OTPStage Viewset"""

    queryset = OTPStage.objects.all()
    serializer_class = OTPStageSerializer
