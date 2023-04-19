"""Prompt Stage API Views"""
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import CharField, ModelSerializer
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.flows.api.stages import StageSerializer
from authentik.flows.challenge import ChallengeTypes, HttpChallengeResponse
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.lib.utils.errors import exception_to_string
from authentik.stages.prompt.models import Prompt, PromptStage
from authentik.stages.prompt.stage import PromptChallenge, PromptStageView


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
            "name",
            "field_key",
            "label",
            "type",
            "required",
            "placeholder",
            "initial_value",
            "order",
            "promptstage_set",
            "sub_text",
            "placeholder_expression",
            "initial_value_expression",
        ]


class PromptViewSet(UsedByMixin, ModelViewSet):
    """Prompt Viewset"""

    queryset = Prompt.objects.all().prefetch_related("promptstage_set")
    serializer_class = PromptSerializer
    filterset_fields = ["field_key", "name", "label", "type", "placeholder"]
    search_fields = ["field_key", "name", "label", "type", "placeholder"]

    @extend_schema(
        request=PromptSerializer,
        responses={
            200: PromptChallenge,
        },
    )
    @action(detail=False, methods=["POST"])
    def preview(self, request: Request) -> Response:
        """Preview a prompt as a challenge, just like a flow would receive"""
        # Remove a couple things from the request, the serializer will fail on these
        # when previewing an existing prompt
        # and since we don't plan to save from this, set a random name and remove the stage
        request.data["name"] = generate_id()
        request.data.pop("promptstage_set", None)
        # Validate data, same as a normal edit/create request
        prompt = PromptSerializer(data=request.data)
        prompt.is_valid(raise_exception=True)
        # Convert serializer to prompt instance
        prompt_model = Prompt(**prompt.validated_data)
        # Convert to field challenge
        try:
            fields = PromptStageView(
                FlowExecutorView(
                    plan=FlowPlan(""),
                    request=request._request,
                ),
                request=request._request,
            ).get_prompt_challenge_fields([prompt_model], {}, dry_run=True)
        except PropertyMappingExpressionException as exc:
            return Response(
                {
                    "non_field_errors": [
                        exception_to_string(exc),
                    ]
                },
                status=400,
            )
        challenge = PromptChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "fields": fields,
            },
        )
        challenge.is_valid()
        return HttpChallengeResponse(challenge)
