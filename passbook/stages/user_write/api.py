"""User Write Stage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.user_write.models import UserWriteStage


class UserWriteStageSerializer(ModelSerializer):
    """UserWriteStage Serializer"""

    class Meta:

        model = UserWriteStage
        fields = [
            "pk",
            "name",
        ]


class UserWriteStageViewSet(ModelViewSet):
    """UserWriteStage Viewset"""

    queryset = UserWriteStage.objects.all()
    serializer_class = UserWriteStageSerializer
