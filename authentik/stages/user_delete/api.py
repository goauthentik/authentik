"""User Delete Stage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.stages.user_delete.models import UserDeleteStage


class UserDeleteStageSerializer(ModelSerializer):
    """UserDeleteStage Serializer"""

    class Meta:

        model = UserDeleteStage
        fields = [
            "pk",
            "name",
        ]


class UserDeleteStageViewSet(ModelViewSet):
    """UserDeleteStage Viewset"""

    queryset = UserDeleteStage.objects.all()
    serializer_class = UserDeleteStageSerializer
