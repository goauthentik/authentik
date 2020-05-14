"""PasswordStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.password.models import PasswordStage


class PasswordStageSerializer(ModelSerializer):
    """PasswordStage Serializer"""

    class Meta:

        model = PasswordStage
        fields = [
            "pk",
            "name",
            "backends",
        ]


class PasswordStageViewSet(ModelViewSet):
    """PasswordStage Viewset"""

    queryset = PasswordStage.objects.all()
    serializer_class = PasswordStageSerializer
