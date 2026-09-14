"""CaptchaStage API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.captcha.models import CaptchaStage


class CaptchaStageSerializer(StageSerializer):
    """CaptchaStage Serializer"""

    class Meta:
        model = CaptchaStage
        fields = StageSerializer.Meta.fields + [
            "public_key",
            "secret",
            "js_url",
            "api_url",
            "request_content_type",
            "interactive",
            "score_min_threshold",
            "score_max_threshold",
            "error_on_invalid_score",
        ]
        extra_kwargs = {
            "secret": {"required": True, "allow_null": False},
        }


class CaptchaStageViewSet(UsedByMixin, ModelViewSet):
    """CaptchaStage Viewset"""

    queryset = CaptchaStage.objects.all()
    serializer_class = CaptchaStageSerializer
    filterset_fields = ["name", "public_key"]
    search_fields = ["name"]
    ordering = ["name"]
