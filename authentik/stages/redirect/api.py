"""RedirectStage API Views"""

from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.redirect.models import RedirectMode, RedirectStage


class RedirectStageSerializer(StageSerializer):
    """RedirectStage Serializer"""

    def validate(self, attrs):
        mode = attrs.get("mode")
        target_static = attrs.get("target_static")
        target_flow = attrs.get("target_flow")
        if mode == RedirectMode.STATIC and not target_static:
            raise ValidationError(_("Target URL should be present when mode is Static."))
        if mode == RedirectMode.FLOW and not target_flow:
            raise ValidationError(_("Target Flow should be present when mode is Flow."))
        return attrs

    class Meta:
        model = RedirectStage
        fields = StageSerializer.Meta.fields + [
            "keep_context",
            "mode",
            "target_static",
            "target_flow",
        ]


class RedirectStageViewSet(UsedByMixin, ModelViewSet):
    """RedirectStage Viewset"""

    queryset = RedirectStage.objects.all()
    serializer_class = RedirectStageSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering = ["name"]
