"""User Create Stage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.user_create.models import UserCreateStage


class UserCreateStageSerializer(ModelSerializer):
    """UserCreateStage Serializer"""

    class Meta:

        model = UserCreateStage
        fields = [
            "pk",
            "name",
        ]


class UserCreateStageViewSet(ModelViewSet):
    """UserCreateStage Viewset"""

    queryset = UserCreateStage.objects.all()
    serializer_class = UserCreateStageSerializer
