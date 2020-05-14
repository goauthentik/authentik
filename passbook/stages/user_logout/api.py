"""Logout Stage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.user_logout.models import UserLogoutStage


class UserLogoutStageSerializer(ModelSerializer):
    """UserLogoutStage Serializer"""

    class Meta:

        model = UserLogoutStage
        fields = [
            "pk",
            "name",
        ]


class UserLogoutStageViewSet(ModelViewSet):
    """UserLogoutStage Viewset"""

    queryset = UserLogoutStage.objects.all()
    serializer_class = UserLogoutStageSerializer
