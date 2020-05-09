"""Login Stage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.login.models import LoginStage


class LoginStageSerializer(ModelSerializer):
    """LoginStage Serializer"""

    class Meta:

        model = LoginStage
        fields = [
            "pk",
            "name",
        ]


class LoginStageViewSet(ModelViewSet):
    """LoginStage Viewset"""

    queryset = LoginStage.objects.all()
    serializer_class = LoginStageSerializer
