"""Prompt Stage API Views"""

from django.db import transaction
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.expression.exceptions import PropertyMappingExpressionException
from authentik.flows.api.stages import StageSerializer
from authentik.flows.challenge import HttpChallengeResponse
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.utils.errors import exception_to_string
from authentik.stages.prompt.models import Prompt, PromptStage, PromptStageField
from authentik.stages.prompt.stage import PromptChallenge, PromptStageView


class PromptStageSerializer(StageSerializer):
    """PromptStage Serializer"""

    @transaction.atomic()
    def _set_fields(self, instance: PromptStage, prompts: list[Prompt]) -> None:
        """Persist the stage's fields with a per-stage order taken from the list position,
        so the order a field is shown in is a property of its use in this stage."""
        PromptStageField.objects.filter(prompt_stage=instance).delete()
        PromptStageField.objects.bulk_create(
            PromptStageField(prompt_stage=instance, prompt=prompt, order=order)
            for order, prompt in enumerate(prompts)
        )

    def create(self, validated_data: dict) -> PromptStage:
        fields = validated_data.pop("fields", [])
        instance = super().create(validated_data)
        self._set_fields(instance, fields)
        return instance

    def update(self, instance: PromptStage, validated_data: dict) -> PromptStage:
        fields = validated_data.pop("fields", None)
        instance = super().update(instance, validated_data)
        if fields is not None:
            self._set_fields(instance, fields)
        return instance

    class Meta:
        model = PromptStage
        fields = StageSerializer.Meta.fields + [
            "fields",
            "validation_policies",
        ]


class PromptStageViewSet(UsedByMixin, ModelViewSet):
    """PromptStage Viewset"""

    queryset = PromptStage.objects.prefetch_related(
        "flow_set",
        # Fields are returned in their per-stage order (PromptStageField.order)
        Prefetch("fields", queryset=Prompt.objects.order_by("promptstagefield__order")),
        "validation_policies",
    ).all()
    serializer_class = PromptStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]

    @extend_schema(
        request=PromptStageSerializer,
        responses={
            200: PromptChallenge,
        },
    )
    @action(detail=False, methods=["POST"])
    def preview(self, request: Request) -> Response:
        """Preview the whole stage as a challenge, just like a flow would receive"""
        # Load the referenced prompts in the order they were submitted, so the preview
        # reflects the per-stage field order being edited.
        prompt_pks = request.data.get("fields", [])
        prompts_by_pk = {str(p.pk): p for p in Prompt.objects.filter(pk__in=prompt_pks)}
        prompt_models = [prompts_by_pk[str(pk)] for pk in prompt_pks if str(pk) in prompts_by_pk]
        try:
            fields = PromptStageView(
                FlowExecutorView(
                    plan=FlowPlan(""),
                    request=request._request,
                ),
                request=request._request,
            ).get_prompt_challenge_fields(prompt_models, {}, dry_run=True)
        except PropertyMappingExpressionException as exc:
            return Response(
                {
                    "non_field_errors": [
                        exception_to_string(exc.exc),
                    ]
                },
                status=400,
            )
        challenge = PromptChallenge(
            data={
                "fields": fields,
            },
        )
        challenge.is_valid()
        return HttpChallengeResponse(challenge)
