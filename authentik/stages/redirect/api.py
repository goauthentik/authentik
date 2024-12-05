"""RedirectStage API Views"""

from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.redirect.models import RedirectStage


class RedirectStageSerializer(StageSerializer):
    """RedirectStage Serializer"""

    def validate(self, attrs):
        target_static = attrs.get("target_static", None)
        target_flow = attrs.get("target_flow", None)
        if not target_static and not target_flow:
            raise ValidationError(_("At least one redirect target should be present."))
        return attrs

    class Meta:
        model = RedirectStage
        fields = StageSerializer.Meta.fields + [
            "keep_context",
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
