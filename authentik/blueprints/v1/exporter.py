"""Flow exporter"""
from typing import Iterator
from uuid import UUID

from django.db.models import Q
from yaml import dump

from authentik.blueprints.v1.common import Blueprint, BlueprintDumper, BlueprintEntry
from authentik.flows.models import Flow, FlowStageBinding, Stage
from authentik.policies.models import Policy, PolicyBinding
from authentik.stages.prompt.models import PromptStage


class Exporter:
    """Export flow with attached stages into yaml"""

    flow: Flow
    with_policies: bool
    with_stage_prompts: bool

    pbm_uuids: list[UUID]

    def __init__(self, flow: Flow):
        self.flow = flow
        self.with_policies = True
        self.with_stage_prompts = True

    def _prepare_pbm(self):
        self.pbm_uuids = [self.flow.pbm_uuid]
        self.pbm_uuids += FlowStageBinding.objects.filter(target=self.flow).values_list(
            "pbm_uuid", flat=True
        )

    def walk_stages(self) -> Iterator[BlueprintEntry]:
        """Convert all stages attached to self.flow into BlueprintEntry objects"""
        stages = Stage.objects.filter(flow=self.flow).select_related().select_subclasses()
        for stage in stages:
            if isinstance(stage, PromptStage):
                pass
            yield BlueprintEntry.from_model(stage, "name")

    def walk_stage_bindings(self) -> Iterator[BlueprintEntry]:
        """Convert all bindings attached to self.flow into BlueprintEntry objects"""
        bindings = FlowStageBinding.objects.filter(target=self.flow).select_related()
        for binding in bindings:
            yield BlueprintEntry.from_model(binding, "target", "stage", "order")

    def walk_policies(self) -> Iterator[BlueprintEntry]:
        """Walk over all policies. This is done at the beginning of the export for stages that have
        a direct foreign key to a policy."""
        # Special case for PromptStage as that has a direct M2M to policy, we have to ensure
        # all policies referenced in there we also include here
        prompt_stages = PromptStage.objects.filter(flow=self.flow).values_list("pk", flat=True)
        query = Q(bindings__in=self.pbm_uuids) | Q(promptstage__in=prompt_stages)
        policies = Policy.objects.filter(query).select_related()
        for policy in policies:
            yield BlueprintEntry.from_model(policy)

    def walk_policy_bindings(self) -> Iterator[BlueprintEntry]:
        """Walk over all policybindings relative to us. This is run at the end of the export, as
        we are sure all objects exist now."""
        bindings = PolicyBinding.objects.filter(target__in=self.pbm_uuids).select_related()
        for binding in bindings:
            yield BlueprintEntry.from_model(binding, "policy", "target", "order")

    def walk_stage_prompts(self) -> Iterator[BlueprintEntry]:
        """Walk over all prompts associated with any PromptStages"""
        prompt_stages = PromptStage.objects.filter(flow=self.flow)
        for stage in prompt_stages:
            for prompt in stage.fields.all():
                yield BlueprintEntry.from_model(prompt)

    def export(self) -> Blueprint:
        """Create a list of all objects including the flow"""
        if self.with_policies:
            self._prepare_pbm()
        bundle = Blueprint()
        bundle.entries.append(BlueprintEntry.from_model(self.flow, "slug"))
        if self.with_stage_prompts:
            bundle.entries.extend(self.walk_stage_prompts())
        if self.with_policies:
            bundle.entries.extend(self.walk_policies())
        bundle.entries.extend(self.walk_stages())
        bundle.entries.extend(self.walk_stage_bindings())
        if self.with_policies:
            bundle.entries.extend(self.walk_policy_bindings())
        return bundle

    def export_to_string(self) -> str:
        """Call export and convert it to yaml"""
        bundle = self.export()
        return dump(bundle, Dumper=BlueprintDumper)
