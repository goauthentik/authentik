"""Flow exporter"""
from json import dumps
from typing import Iterator

from passbook.flows.models import Flow, FlowStageBinding, Stage
from passbook.flows.transfer.common import DataclassEncoder, FlowBundle, FlowBundleEntry
from passbook.policies.models import Policy, PolicyBinding, PolicyBindingModel
from passbook.stages.prompt.models import PromptStage


class FlowExporter:
    """Export flow with attached stages into json"""

    flow: Flow
    with_policies: bool
    with_stage_prompts: bool

    def __init__(self, flow: Flow):
        self.flow = flow
        self.with_policies = True
        self.with_stage_prompts = True

    def walk_stages(self) -> Iterator[FlowBundleEntry]:
        """Convert all stages attached to self.flow into FlowBundleEntry objects"""
        stages = (
            Stage.objects.filter(flow=self.flow).select_related().select_subclasses()
        )
        for stage in stages:
            if isinstance(stage, PromptStage):
                pass
            yield FlowBundleEntry.from_model(stage, "name")

    def walk_stage_bindings(self) -> Iterator[FlowBundleEntry]:
        """Convert all bindings attached to self.flow into FlowBundleEntry objects"""
        bindings = FlowStageBinding.objects.filter(target=self.flow).select_related()
        for binding in bindings:
            yield FlowBundleEntry.from_model(binding, "target", "stage", "order")

    def walk_policies(self) -> Iterator[FlowBundleEntry]:
        """Walk over all policies and their respective bindings"""
        pbm_uuids = [self.flow.pbm_uuid]
        for stage_subclass in Stage.__subclasses__():
            if issubclass(stage_subclass, PolicyBindingModel):
                pbm_uuids += stage_subclass.objects.filter(flow=self.flow).values_list(
                    "pbm_uuid", flat=True
                )
        pbm_uuids += FlowStageBinding.objects.filter(target=self.flow).values_list(
            "pbm_uuid", flat=True
        )
        policies = Policy.objects.filter(bindings__in=pbm_uuids).select_related()
        for policy in policies:
            yield FlowBundleEntry.from_model(policy)
        bindings = PolicyBinding.objects.filter(target__in=pbm_uuids).select_related()
        for binding in bindings:
            yield FlowBundleEntry.from_model(binding)

    def walk_stage_prompts(self) -> Iterator[FlowBundleEntry]:
        """Walk over all prompts associated with any PromptStages"""
        prompt_stages = PromptStage.objects.filter(flow=self.flow)
        for stage in prompt_stages:
            for prompt in stage.fields.all():
                yield FlowBundleEntry.from_model(prompt)

    def export(self) -> FlowBundle:
        """Create a list of all objects including the flow"""
        bundle = FlowBundle()
        bundle.entries.append(FlowBundleEntry.from_model(self.flow, "slug"))
        if self.with_stage_prompts:
            bundle.entries.extend(self.walk_stage_prompts())
        bundle.entries.extend(self.walk_stages())
        bundle.entries.extend(self.walk_stage_bindings())
        if self.with_policies:
            bundle.entries.extend(self.walk_policies())
        return bundle

    def export_to_string(self) -> str:
        """Call export and convert it to json"""
        return dumps(self.export(), cls=DataclassEncoder)
