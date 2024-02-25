"""Source Stage API Views"""

from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.models import Source
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.stages.source.models import SourceStage
from authentik.flows.api.stages import StageSerializer


class SourceStageSerializer(EnterpriseRequiredMixin, StageSerializer):
    """SourceStage Serializer"""

    def validate_source(self, _source: Source) -> Source:
        """Ensure configured source supports web-based login"""
        source = Source.objects.filter(pk=_source.pk).select_subclasses().first()
        if not source:
            raise ValidationError("Invalid source")
        login_button = source.ui_login_button(self.context["request"])
        if not login_button:
            raise ValidationError("Invalid source selected, only web-based sources are supported.")
        return source

    class Meta:
        model = SourceStage
        fields = StageSerializer.Meta.fields + ["source", "resume_timeout"]


class SourceStageViewSet(UsedByMixin, ModelViewSet):
    """SourceStage Viewset"""

    queryset = SourceStage.objects.all()
    serializer_class = SourceStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
