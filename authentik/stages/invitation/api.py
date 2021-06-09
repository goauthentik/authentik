"""Invitation Stage API Views"""
from rest_framework.fields import JSONField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserSerializer
from authentik.core.api.utils import is_dict
from authentik.flows.api.stages import StageSerializer
from authentik.stages.invitation.models import Invitation, InvitationStage


class InvitationStageSerializer(StageSerializer):
    """InvitationStage Serializer"""

    class Meta:

        model = InvitationStage
        fields = StageSerializer.Meta.fields + [
            "continue_flow_without_invitation",
        ]


class InvitationStageViewSet(UsedByMixin, ModelViewSet):
    """InvitationStage Viewset"""

    queryset = InvitationStage.objects.all()
    serializer_class = InvitationStageSerializer


class InvitationSerializer(ModelSerializer):
    """Invitation Serializer"""

    created_by = UserSerializer(read_only=True)
    fixed_data = JSONField(validators=[is_dict], required=False)

    class Meta:

        model = Invitation
        fields = [
            "pk",
            "expires",
            "fixed_data",
            "created_by",
            "single_use",
        ]


class InvitationViewSet(UsedByMixin, ModelViewSet):
    """Invitation Viewset"""

    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    order = ["-expires"]
    search_fields = ["created_by__username", "expires"]
    filterset_fields = ["created_by__username", "expires"]

    def perform_create(self, serializer: InvitationSerializer):
        serializer.save(created_by=self.request.user)
