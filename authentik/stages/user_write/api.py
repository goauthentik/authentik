"""User Write Stage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api import StageSerializer
from authentik.stages.user_write.models import UserWriteStage


class UserWriteStageSerializer(StageSerializer):
    """UserWriteStage Serializer"""

    class Meta:

        model = UserWriteStage
        fields = StageSerializer.Meta.fields


class UserWriteStageViewSet(ModelViewSet):
    """UserWriteStage Viewset"""

    queryset = UserWriteStage.objects.all()
    serializer_class = UserWriteStageSerializer
