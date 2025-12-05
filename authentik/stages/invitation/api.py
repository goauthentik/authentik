"""Invitation Stage API Views"""

from django_filters.filters import BooleanFilter
from django_filters.filterset import FilterSet
from guardian.shortcuts import get_anonymous_user
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.viewsets import ModelViewSet

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import JSONDictField, ModelSerializer
from authentik.core.models import User
from authentik.flows.api.flows import FlowSerializer
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

    created_by = PartialUserSerializer(read_only=True)
    fixed_data = JSONDictField(required=False)
    flow_obj = FlowSerializer(read_only=True, required=False, source="flow")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            self.fields["created_by"] = PrimaryKeyRelatedField(
                queryset=User.objects.all(),
                required=False,
                allow_null=True,
                default=get_anonymous_user(),
            )

    class Meta:
        model = Invitation
        fields = [
            "pk",
            "name",
            "expires",
            "fixed_data",
            "created_by",
            "single_use",
            "flow",
            "flow_obj",
        ]


class InvitationViewSet(UsedByMixin, ModelViewSet):
    """Invitation Viewset"""

    queryset = Invitation.objects.including_expired().all()
    serializer_class = InvitationSerializer
    ordering = ["-expires"]
    search_fields = ["name", "created_by__username", "expires", "flow__slug"]
    filterset_fields = ["name", "created_by__username", "expires", "flow__slug"]

    def perform_create(self, serializer: InvitationSerializer):
        kwargs = {}
        if SERIALIZER_CONTEXT_BLUEPRINT not in serializer.context:
            kwargs["created_by"] = self.request.user
        serializer.save(**kwargs)
