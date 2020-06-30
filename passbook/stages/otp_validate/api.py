"""OTPValidateStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.otp_validate.models import OTPValidateStage


class OTPValidateStageSerializer(ModelSerializer):
    """OTPValidateStage Serializer"""

    class Meta:

        model = OTPValidateStage
        fields = [
            "pk",
            "name",
        ]


class OTPValidateStageViewSet(ModelViewSet):
    """OTPValidateStage Viewset"""

    queryset = OTPValidateStage.objects.all()
    serializer_class = OTPValidateStageSerializer
