from dataclasses import dataclass, field

from django.db import models
from django.db.models import Model, QuerySet
from guardian.shortcuts import get_objects_for_user
from rest_framework.fields import CharField, ChoiceField, IntegerField

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.flows.models import (
    Flow,
    FlowAuthenticationRequirement,
    FlowStageBinding,
)
from authentik.policies.models import PolicyBinding, PolicyBindingModel


class DiagramNodeTypes(models.TextChoices):

    FLOW_START = "flow-start"
    PRE_FLOW_POLICIES = "pre-flow-policies"
    AUTHENTICATION_REQUIREMENT = "authentication-requirement"
    STAGE = "stage"
    POLICY = "policy"
    FLOW_END = "flow-end"


class DiagramEdgeTypes(models.TextChoices):

    PROCEED = "proceed"
    BINDING = "binding"
    POLICY_PASSED = "policy-passed"
    POLICY_DENIED = "policy-denied"
    REQUIREMENT_FULFILLED = "requirement-fulfilled"
    REQUIREMENT_UNFULFILLED = "requirement-unfulfilled"


def model_label(instance: Model) -> str:
    return f"{instance._meta.app_label}.{instance._meta.model_name}"


@dataclass
class DiagramNode:

    identifier: str
    type: DiagramNodeTypes

    name: str = ""
    verbose_name: str = ""

    model: str = ""
    pk: str = ""

    component: str = ""

    # The binding lookup
    binding_model: str = ""
    binding_pk: str = ""
    binding_order: int | None = None


@dataclass
class DiagramEdge:

    source: str
    target: str
    type: DiagramEdgeTypes = DiagramEdgeTypes.PROCEED


@dataclass
class DiagramGraph:

    nodes: list[DiagramNode] = field(default_factory=list)
    edges: list[DiagramEdge] = field(default_factory=list)


def stage_node(identifier: str, binding: FlowStageBinding) -> DiagramNode:
    stage = binding.stage
    return DiagramNode(
        identifier=identifier,
        type=DiagramNodeTypes.STAGE,
        name=stage.name,
        verbose_name=str(stage._meta.verbose_name),
        model=model_label(stage),
        pk=str(stage.pk),
        component=stage.component,
        binding_model=model_label(binding),
        binding_pk=str(binding.pk),
        binding_order=binding.order,
    )


def policy_node(identifier: str, binding: PolicyBinding) -> DiagramNode:
    policy = binding.policy
    return DiagramNode(
        identifier=identifier,
        type=DiagramNodeTypes.POLICY,
        name=policy.name,
        verbose_name=str(policy._meta.verbose_name),
        model=model_label(policy),
        pk=str(policy.pk),
        component=policy.component,
        binding_model=model_label(binding),
        binding_pk=str(binding.pk),
        binding_order=binding.order,
    )


class FlowDiagram:
    flow: Flow
    user: User
    graph: DiagramGraph

    def __init__(self, flow: Flow, user: User) -> None:
        self.flow = flow
        self.user = user
        self.graph = DiagramGraph()

    def add_node(self, node: DiagramNode) -> DiagramNode:
        self.graph.nodes.append(node)
        return node

    # This confused me the first time, so: first you add the new node, THEN you add all the edges
    # FROM its sources to it.
    def add_edges(
        self,
        sources: list[DiagramNode],
        target: DiagramNode,
        type: DiagramEdgeTypes = DiagramEdgeTypes.PROCEED,
    ) -> None:
        for source in sources:
            self.graph.edges.append(DiagramEdge(source.identifier, target.identifier, type))

    def get_policy_bindings(self, target: PolicyBindingModel) -> QuerySet[PolicyBinding]:
        return (
            get_objects_for_user(self.user, "authentik_policies.view_policybinding")
            .filter(target=target)
            .exclude(policy__isnull=True)
            .order_by("order")
        )

    def get_authentication_requirement(self, flow_start: DiagramNode, end: DiagramNode) -> None:
        if self.flow.authentication == FlowAuthenticationRequirement.NONE:
            return

        requirement = self.add_node(
            DiagramNode(
                identifier="flow_auth_requirement",
                type=DiagramNodeTypes.AUTHENTICATION_REQUIREMENT,
                name=self.flow.authentication,
            )
        )
        self.add_edges([requirement], end, DiagramEdgeTypes.REQUIREMENT_UNFULFILLED)
        self.add_edges([requirement], flow_start, DiagramEdgeTypes.REQUIREMENT_FULFILLED)

    def get_flow_policies(self, flow_start: DiagramNode, end: DiagramNode) -> None:
        bindings = list(self.get_policy_bindings(self.flow))

        if not bindings:
            return

        pre = self.add_node(
            DiagramNode(identifier="flow_pre", type=DiagramNodeTypes.PRE_FLOW_POLICIES)
        )

        for index, binding in enumerate(bindings):
            policy = self.add_node(policy_node(f"flow_policy_{index}", binding))

            self.add_edges([pre], policy, DiagramEdgeTypes.BINDING)
            self.add_edges([policy], end, DiagramEdgeTypes.POLICY_DENIED)
            self.add_edges([policy], flow_start)

    def get_stages(self, flow_start: DiagramNode) -> DiagramNode:
        parents = [flow_start]
        previous_policies: list[DiagramNode] = []
        last_stage: DiagramNode | None = None

        stages = (
            get_objects_for_user(self.user, "authentik_flows.view_flowstagebinding")
            .filter(target=self.flow)
            .order_by("order")
        )

        # This loop really gives away the linear nature of our DSL.
        for stage_index, stage_binding in enumerate(stages):
            policies = []
            raw_policies = enumerate(self.get_policy_bindings(stage_binding))
            for policy_index, policy_binding in raw_policies:
                policies.append(
                    self.add_node(
                        policy_node(
                            f"stage_{stage_index}_policy_{policy_index}",
                            policy_binding,
                        )
                    )
                )

            stage = self.add_node(stage_node(f"stage_{stage_index}", stage_binding))

            for policy in policies:
                self.add_edges(parents, policy)

            if policies:
                self.add_edges(policies, stage, DiagramEdgeTypes.POLICY_PASSED)
            else:
                self.add_edges(parents, stage)

            self.add_edges(previous_policies, stage, DiagramEdgeTypes.POLICY_DENIED)

            parents, previous_policies, last_stage = [stage], policies, stage

        return last_stage or flow_start

    def build(self) -> DiagramGraph:
        flow_start = DiagramNode(
            identifier="flow_start",
            type=DiagramNodeTypes.FLOW_START,
            name=self.flow.name,
        )

        end = DiagramNode(identifier="done", type=DiagramNodeTypes.FLOW_END)
        self.get_authentication_requirement(flow_start, end)
        self.get_flow_policies(flow_start, end)
        self.add_node(flow_start)

        exit_node = self.get_stages(flow_start)

        self.add_node(end)
        self.add_edges([exit_node], end)

        return self.graph


class DiagramNodeSerializer(PassiveSerializer):

    identifier = CharField(read_only=True)
    type = ChoiceField(choices=DiagramNodeTypes.choices, read_only=True)
    name = CharField(read_only=True, allow_blank=True)
    verbose_name = CharField(read_only=True, allow_blank=True)

    model = CharField(read_only=True, allow_blank=True)
    pk = CharField(read_only=True, allow_blank=True)
    component = CharField(read_only=True, allow_blank=True)

    binding_model = CharField(read_only=True, allow_blank=True)
    binding_pk = CharField(read_only=True, allow_blank=True)
    binding_order = IntegerField(read_only=True, allow_null=True)


class DiagramEdgeSerializer(PassiveSerializer):

    # Can't call it "source" at the serialization layer as that's a keyword in the serializer base
    # class
    origin = CharField(source="source", read_only=True)
    target = CharField(read_only=True)
    type = ChoiceField(choices=DiagramEdgeTypes.choices, read_only=True)


class FlowDiagramSerializer(PassiveSerializer):

    nodes = DiagramNodeSerializer(many=True, read_only=True)
    edges = DiagramEdgeSerializer(many=True, read_only=True)
