"""Login Stage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.user_login.models import UserLoginStage


class UserLoginStageSerializer(ModelSerializer):
    """UserLoginStage Serializer"""

    class Meta:

        model = UserLoginStage
        fields = [
            "pk",
            "name",
        ]


class UserLoginStageViewSet(ModelViewSet):
    """UserLoginStage Viewset"""

    queryset = UserLoginStage.objects.all()
    serializer_class = UserLoginStageSerializer
