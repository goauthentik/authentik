"""Logout Stage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.user_logout.models import UserLogoutStage


class UserLogoutStageSerializer(StageSerializer):
    """UserLogoutStage Serializer"""

    class Meta:

        model = UserLogoutStage
        fields = StageSerializer.Meta.fields


class UserLogoutStageViewSet(UsedByMixin, ModelViewSet):
    """UserLogoutStage Viewset"""

    queryset = UserLogoutStage.objects.all()
    serializer_class = UserLogoutStageSerializer
    filterset_fields = "__all__"
    search_fields = ["name"]
    ordering = ["name"]
