"""Prompt Stage API Views"""
from rest_framework.serializers import CharField, ModelSerializer
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet

from passbook.stages.prompt.models import Prompt, PromptStage


class PromptStageSerializer(ModelSerializer):
    """PromptStage Serializer"""

    name = CharField(validators=[UniqueValidator(queryset=PromptStage.objects.all())])

    class Meta:

        model = PromptStage
        fields = [
            "pk",
            "name",
            "fields",
        ]


class PromptStageViewSet(ModelViewSet):
    """PromptStage Viewset"""

    queryset = PromptStage.objects.all()
    serializer_class = PromptStageSerializer


class PromptSerializer(ModelSerializer):
    """Prompt Serializer"""

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
        ]


class PromptViewSet(ModelViewSet):
    """Prompt Viewset"""

    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
