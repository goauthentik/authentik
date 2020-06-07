"""ConsentStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.consent.models import ConsentStage


class ConsentStageSerializer(ModelSerializer):
    """ConsentStage Serializer"""

    class Meta:

        model = ConsentStage
        fields = ["pk", "name"]


class ConsentStageViewSet(ModelViewSet):
    """ConsentStage Viewset"""

    queryset = ConsentStage.objects.all()
    serializer_class = ConsentStageSerializer
