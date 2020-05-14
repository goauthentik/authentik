"""Invitation Stage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.invitation.models import Invitation, InvitationStage


class InvitationStageSerializer(ModelSerializer):
    """InvitationStage Serializer"""

    class Meta:

        model = InvitationStage
        fields = [
            "pk",
            "name",
            "continue_flow_without_invitation",
        ]


class InvitationStageViewSet(ModelViewSet):
    """InvitationStage Viewset"""

    queryset = InvitationStage.objects.all()
    serializer_class = InvitationStageSerializer


class InvitationSerializer(ModelSerializer):
    """Invitation Serializer"""

    class Meta:

        model = Invitation
        fields = [
            "pk",
            "expires",
            "fixed_data",
        ]


class InvitationViewSet(ModelViewSet):
    """Invitation Viewset"""

    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
