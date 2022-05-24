"""Prompt Stage API Views"""
from rest_framework.serializers import CharField, ModelSerializer
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.prompt.models import Prompt, PromptStage


class PromptStageSerializer(StageSerializer):
    """PromptStage Serializer"""

    name = CharField(validators=[UniqueValidator(queryset=PromptStage.objects.all())])

    class Meta:

        model = PromptStage
        fields = StageSerializer.Meta.fields + [
            "fields",
            "validation_policies",
        ]


class PromptStageViewSet(UsedByMixin, ModelViewSet):
    """PromptStage Viewset"""

    queryset = PromptStage.objects.all()
    serializer_class = PromptStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]


class PromptSerializer(ModelSerializer):
    """Prompt Serializer"""

    promptstage_set = StageSerializer(many=True, required=False)

    class Meta:

        model = Prompt
        fields = [
            "pk",
            "field_key",
            "label",
            "type",
            "required",
            "placeholder",
            "order",
            "promptstage_set",
            "sub_text",
            "placeholder_expression",
        ]


class PromptViewSet(UsedByMixin, ModelViewSet):
    """Prompt Viewset"""

    queryset = Prompt.objects.all().prefetch_related("promptstage_set")
    serializer_class = PromptSerializer
    filterset_fields = ["field_key", "label", "type", "placeholder"]
    search_fields = ["field_key", "label", "type", "placeholder"]
