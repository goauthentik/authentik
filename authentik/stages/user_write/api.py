"""User Write Stage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.user_write.models import UserWriteStage


class UserWriteStageSerializer(StageSerializer):
    """UserWriteStage Serializer"""

    class Meta:

        model = UserWriteStage
        fields = StageSerializer.Meta.fields


from authentik.core.api.used_by import UsedByMixin


class UserWriteStageViewSet(UsedByMixin, ModelViewSet):
    """UserWriteStage Viewset"""

    queryset = UserWriteStage.objects.all()
    serializer_class = UserWriteStageSerializer
