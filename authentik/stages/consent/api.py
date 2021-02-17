"""ConsentStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api import StageSerializer
from authentik.stages.consent.models import ConsentStage


class ConsentStageSerializer(StageSerializer):
    """ConsentStage Serializer"""

    class Meta:

        model = ConsentStage
        fields = StageSerializer.Meta.fields + ["mode", "consent_expire_in"]


class ConsentStageViewSet(ModelViewSet):
    """ConsentStage Viewset"""

    queryset = ConsentStage.objects.all()
    serializer_class = ConsentStageSerializer
