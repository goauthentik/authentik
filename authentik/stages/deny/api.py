"""deny Stage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.deny.models import DenyStage


class DenyStageSerializer(StageSerializer):
    """DenyStage Serializer"""

    class Meta:

        model = DenyStage
        fields = StageSerializer.Meta.fields


class DenyStageViewSet(ModelViewSet):
    """DenyStage Viewset"""

    queryset = DenyStage.objects.all()
    serializer_class = DenyStageSerializer
