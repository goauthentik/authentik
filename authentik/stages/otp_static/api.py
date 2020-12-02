"""OTPStaticStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.stages.otp_static.models import OTPStaticStage


class OTPStaticStageSerializer(ModelSerializer):
    """OTPStaticStage Serializer"""

    class Meta:

        model = OTPStaticStage
        fields = ["pk", "name", "configure_flow", "token_count"]


class OTPStaticStageViewSet(ModelViewSet):
    """OTPStaticStage Viewset"""

    queryset = OTPStaticStage.objects.all()
    serializer_class = OTPStaticStageSerializer
