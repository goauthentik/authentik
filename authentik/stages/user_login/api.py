"""Login Stage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.user_login.models import UserLoginStage


class UserLoginStageSerializer(StageSerializer):
    """UserLoginStage Serializer"""

    class Meta:

        model = UserLoginStage
        fields = StageSerializer.Meta.fields + [
            "session_duration",
        ]


class UserLoginStageViewSet(UsedByMixin, ModelViewSet):
    """UserLoginStage Viewset"""

    queryset = UserLoginStage.objects.all()
    serializer_class = UserLoginStageSerializer
    filterset_fields = "__all__"
    search_fields = ["name"]
    ordering = ["name"]
