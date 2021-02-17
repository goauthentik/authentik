"""User Delete Stage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api import StageSerializer
from authentik.stages.user_delete.models import UserDeleteStage


class UserDeleteStageSerializer(StageSerializer):
    """UserDeleteStage Serializer"""

    class Meta:

        model = UserDeleteStage
        fields = StageSerializer.Meta.fields


class UserDeleteStageViewSet(ModelViewSet):
    """UserDeleteStage Viewset"""

    queryset = UserDeleteStage.objects.all()
    serializer_class = UserDeleteStageSerializer
