"""Blueprint exporter"""

from collections.abc import Iterable
from uuid import UUID

from django.apps import apps
from django.db.models import Model, Q, QuerySet
from django.utils.timezone import now
from django.utils.translation import gettext as _
from yaml import dump

from authentik.blueprints.v1.common import (
    Blueprint,
    BlueprintDumper,
    BlueprintEntry,
    BlueprintMetadata,
)
from authentik.blueprints.v1.importer import is_model_allowed
from authentik.blueprints.v1.labels import LABEL_AUTHENTIK_GENERATED
from authentik.events.models import Event
from authentik.flows.models import Flow, FlowStageBinding, Stage
from authentik.policies.models import Policy, PolicyBinding
from authentik.stages.prompt.models import PromptStage


class Exporter:
    """Export flow with attached stages into yaml"""

    excluded_models: list[type[Model]] = []

    def __init__(self):
        self.excluded_models = [
            Event,
        ]

    def get_entries(self) -> Iterable[BlueprintEntry]:
        """Get blueprint entries"""
        for model in apps.get_models():
            if not is_model_allowed(model):
                continue
            if model in self.excluded_models:
                continue
            for obj in self.get_model_instances(model):
                yield BlueprintEntry.from_model(obj)

    def get_model_instances(self, model: type[Model]) -> QuerySet:
        """Return a queryset for `model`. Can be used to filter some
        objects on some models"""
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

    def walk_stages(self) -> Iterable[BlueprintEntry]:
        """Convert all stages attached to self.flow into BlueprintEntry objects"""
        stages = Stage.objects.filter(flow=self.flow).select_related().select_subclasses()
        for stage in stages:
            if isinstance(stage, PromptStage):
                pass
            yield BlueprintEntry.from_model(stage, "name")

    def walk_stage_bindings(self) -> Iterable[BlueprintEntry]:
        """Convert all bindings attached to self.flow into BlueprintEntry objects"""
        bindings = FlowStageBinding.objects.filter(target=self.flow).select_related()
        for binding in bindings:
            yield BlueprintEntry.from_model(binding, "target", "stage", "order")

    def walk_policies(self) -> Iterable[BlueprintEntry]:
        """Walk over all policies. This is done at the beginning of the export for stages that have
        a direct foreign key to a policy."""
        # Special case for PromptStage as that has a direct M2M to policy, we have to ensure
        # all policies referenced in there we also include here
        prompt_stages = PromptStage.objects.filter(flow=self.flow).values_list("pk", flat=True)
        query = Q(bindings__in=self.pbm_uuids) | Q(promptstage__in=prompt_stages)
        policies = Policy.objects.filter(query).select_related()
        for policy in policies:
            yield BlueprintEntry.from_model(policy)

    def walk_policy_bindings(self) -> Iterable[BlueprintEntry]:
        """Walk over all policybindings relative to us. This is run at the end of the export, as
        we are sure all objects exist now."""
        bindings = PolicyBinding.objects.filter(target__in=self.pbm_uuids).select_related()
        for binding in bindings:
            yield BlueprintEntry.from_model(binding, "policy", "target", "order")

    def walk_stage_prompts(self) -> Iterable[BlueprintEntry]:
        """Walk over all prompts associated with any PromptStages"""
        prompt_stages = PromptStage.objects.filter(flow=self.flow)
        for stage in prompt_stages:
            for prompt in stage.fields.all():
                yield BlueprintEntry.from_model(prompt)

    def get_entries(self) -> Iterable[BlueprintEntry]:
        entries = []
        entries.append(BlueprintEntry.from_model(self.flow, "slug"))
        if self.with_stage_prompts:
            entries.extend(self.walk_stage_prompts())
        if self.with_policies:
            entries.extend(self.walk_policies())
        entries.extend(self.walk_stages())
        entries.extend(self.walk_stage_bindings())
        if self.with_policies:
            entries.extend(self.walk_policy_bindings())
        return entries
