"""deny Stage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.deny.models import DenyStage


class DenyStageSerializer(StageSerializer):
    """DenyStage Serializer"""

    class Meta:

        model = DenyStage
        fields = StageSerializer.Meta.fields


from authentik.core.api.used_by import UsedByMixin


class DenyStageViewSet(UsedByMixin, ModelViewSet):
    """DenyStage Viewset"""

    queryset = DenyStage.objects.all()
    serializer_class = DenyStageSerializer
