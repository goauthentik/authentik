"""Blueprint exporter"""

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import Model, Q, QuerySet
from django.utils.timezone import now
from django.utils.translation import gettext as _
from yaml import dump

from authentik.blueprints.v1.common import (
    Blueprint,
    BlueprintDumper,
    BlueprintEntry,
    BlueprintMetadata,
    ReferenceIndex,
)
from authentik.blueprints.v1.importer import is_model_allowed
from authentik.blueprints.v1.labels import LABEL_AUTHENTIK_GENERATED
from authentik.events.models import Event
from authentik.flows.models import Flow, FlowStageBinding, Stage
from authentik.policies.models import Policy, PolicyBinding
from authentik.stages.prompt.models import Prompt, PromptStage


class Exporter:
    """Export flow with attached stages into yaml"""

    excluded_models: list[type[Model]] = []

    def __init__(self):
        self.excluded_models = [
            Event,
        ]

    def get_entries(self) -> Iterable[BlueprintEntry]:
        """Get blueprint entries"""
        reference_index = ReferenceIndex()
        instances: list[Model] = []
        for model in apps.get_models():
            if not is_model_allowed(model):
                continue
            if model in self.excluded_models:
                continue
            for obj in self.get_model_instances(model):
                instances.append(obj)
                reference_index.register(obj)
        entries = [
            BlueprintEntry.from_model(obj, reference_index=reference_index) for obj in instances
        ]
        reference_index.clear_unused_ids(entries, instances)
        return entries

    def get_model_instances(self, model: type[Model]) -> QuerySet:
        """Return a queryset for `model`. Can be used to filter some
        objects on some models"""
        if model == get_user_model():
            return model.objects.exclude_anonymous()
        return model.objects.all()

    def _pre_export(self, blueprint: Blueprint):
        """Hook to run anything pre-export"""

    def export(self) -> Blueprint:
        """Create a list of all objects and create a blueprint"""
        blueprint = Blueprint()
        self._pre_export(blueprint)
        blueprint.metadata = BlueprintMetadata(
            name=_("authentik Export - {date}".format_map({"date": str(now())})),
            labels={
                LABEL_AUTHENTIK_GENERATED: "true",
            },
        )
        blueprint.entries = list(self.get_entries())
        return blueprint

    def export_to_string(self) -> str:
        """Call export and convert it to yaml"""
        blueprint = self.export()
        return dump(blueprint, Dumper=BlueprintDumper)


class FlowExporter(Exporter):
    """Exporter customized to only return objects related to `flow`"""

    flow: Flow
    with_policies: bool
    with_stage_prompts: bool

    pbm_uuids: list[UUID]

    def __init__(self, flow: Flow):
        super().__init__()
        self.flow = flow
        self.with_policies = True
        self.with_stage_prompts = True

    def _pre_export(self, blueprint: Blueprint):
        if not self.with_policies:
            return
        self.pbm_uuids = [self.flow.pbm_uuid]
        self.pbm_uuids += FlowStageBinding.objects.filter(target=self.flow).values_list(
            "pbm_uuid", flat=True
        )

    def _stages(self) -> Iterable[Stage]:
        """Get all stages attached to self.flow"""
        return Stage.objects.filter(flow=self.flow).select_related().select_subclasses()

    def _stage_bindings(self) -> Iterable[FlowStageBinding]:
        """Get all bindings attached to self.flow"""
        return FlowStageBinding.objects.filter(target=self.flow).select_related()

    def _policies(self) -> Iterable[Policy]:
        """Get all policies. This is done at the beginning of the export for stages that have
        a direct foreign key to a policy."""
        # Special case for PromptStage as that has a direct M2M to policy, we have to ensure
        # all policies referenced in there we also include here
        prompt_stages = PromptStage.objects.filter(flow=self.flow).values_list("pk", flat=True)
        query = Q(bindings__in=self.pbm_uuids) | Q(promptstage__in=prompt_stages)
        return Policy.objects.filter(query).select_related()

    def _policy_bindings(self) -> Iterable[PolicyBinding]:
        """Get all policybindings relative to us. This is run at the end of the export, as
        we are sure all objects exist now."""
        return PolicyBinding.objects.filter(target__in=self.pbm_uuids).select_related()

    def _stage_prompts(self) -> Iterable[Prompt]:
        """Get all prompts associated with any PromptStages, deduplicated as multiple stages
        may share the same prompt"""
        prompt_stages = PromptStage.objects.filter(flow=self.flow)
        prompts: dict[Any, Prompt] = {}
        for stage in prompt_stages:
            for prompt in stage.fields.all():
                prompts[prompt.pk] = prompt
        return prompts.values()

    def get_entries(self) -> Iterable[BlueprintEntry]:
        reference_index = ReferenceIndex()
        reference_index.register(self.flow)

        prompts = list(self._stage_prompts()) if self.with_stage_prompts else []
        policies = list(self._policies()) if self.with_policies else []
        stages = list(self._stages())
        stage_bindings = list(self._stage_bindings())
        policy_bindings = list(self._policy_bindings()) if self.with_policies else []

        for obj in (*prompts, *policies, *stages, *stage_bindings, *policy_bindings):
            reference_index.register(obj)

        objects = [self.flow, *prompts, *policies, *stages, *stage_bindings, *policy_bindings]
        entries = [
            BlueprintEntry.from_model(self.flow, reference_index=reference_index),
            *(
                BlueprintEntry.from_model(prompt, reference_index=reference_index)
                for prompt in prompts
            ),
            *(
                BlueprintEntry.from_model(policy, reference_index=reference_index)
                for policy in policies
            ),
            *(
                BlueprintEntry.from_model(stage, reference_index=reference_index)
                for stage in stages
            ),
            *(
                BlueprintEntry.from_model(binding, reference_index=reference_index)
                for binding in stage_bindings
            ),
            *(
                BlueprintEntry.from_model(binding, reference_index=reference_index)
                for binding in policy_bindings
            ),
        ]
        reference_index.clear_unused_ids(entries, objects)
        return entries
