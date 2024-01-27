"""Source Stage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.source.models import SourceStage


class SourceStageSerializer(StageSerializer):
    """SourceStage Serializer"""

    # TODO: validate that source is web-based so it can be done in a flow
    # i.e. oauth/saml/plex
    # ideally in a generic way

    class Meta:
        model = SourceStage
        fields = StageSerializer.Meta.fields + ["source", "return_timeout"]


class SourceStageViewSet(UsedByMixin, ModelViewSet):
    """SourceStage Viewset"""

    queryset = SourceStage.objects.all()
    serializer_class = SourceStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
