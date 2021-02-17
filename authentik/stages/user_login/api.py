"""Login Stage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api import StageSerializer
from authentik.stages.user_login.models import UserLoginStage


class UserLoginStageSerializer(StageSerializer):
    """UserLoginStage Serializer"""

    class Meta:

        model = UserLoginStage
        fields = StageSerializer.Meta.fields + [
            "session_duration",
        ]


class UserLoginStageViewSet(ModelViewSet):
    """UserLoginStage Viewset"""

    queryset = UserLoginStage.objects.all()
    serializer_class = UserLoginStageSerializer
