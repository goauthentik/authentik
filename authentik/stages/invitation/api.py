"""Invitation Stage API Views"""
from django_filters.filters import BooleanFilter
from django_filters.filterset import FilterSet
from rest_framework.fields import JSONField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
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


class InvitationStageFilter(FilterSet):
    """invitation filter"""

    no_flows = BooleanFilter("flow", "isnull")

    class Meta:

        model = InvitationStage
        fields = ["name", "no_flows", "continue_flow_without_invitation", "stage_uuid"]


class InvitationStageViewSet(UsedByMixin, ModelViewSet):
    """InvitationStage Viewset"""

    queryset = InvitationStage.objects.all()
    serializer_class = InvitationStageSerializer
    filterset_class = InvitationStageFilter
    ordering = ["name"]
    search_fields = ["name"]


class InvitationSerializer(ModelSerializer):
    """Invitation Serializer"""

    created_by = GroupMemberSerializer(read_only=True)
    fixed_data = JSONField(validators=[is_dict], required=False)

    class Meta:

        model = Invitation
        fields = [
            "pk",
            "name",
            "expires",
            "fixed_data",
            "created_by",
            "single_use",
        ]


class InvitationViewSet(UsedByMixin, ModelViewSet):
    """Invitation Viewset"""

    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    ordering = ["-expires"]
    search_fields = ["name", "created_by__username", "expires"]
    filterset_fields = ["name", "created_by__username", "expires"]

    def perform_create(self, serializer: InvitationSerializer):
        serializer.save(created_by=self.request.user)
