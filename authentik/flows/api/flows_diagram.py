"""Flows Diagram API"""
from dataclasses import dataclass
from typing import Optional

from django.utils.translation import gettext as _
from guardian.shortcuts import get_objects_for_user
from rest_framework.serializers import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.flows.models import Flow, FlowStageBinding


@dataclass
class DiagramElement:
    """Single element used in a diagram"""

    identifier: str
    description: str
    action: Optional[str] = None
    source: Optional[list["DiagramElement"]] = None

    def __str__(self) -> str:
        element = f'{self.identifier}["{self.description}"]'
        if self.action is not None:
            if self.action != "":
                element = f"--{self.action}--> {element}"
            else:
                element = f"--> {element}"
        if self.source:
            source_element = []
            for source in self.source:
                source_element.append(f"{source.identifier} {element}")
            return "\n".join(source_element)
        return element


class FlowDiagramSerializer(PassiveSerializer):
    """response of the flow's diagram action"""

    diagram = CharField(read_only=True)


class FlowDiagram:
    """Generate flow chart fow a flow"""

    flow: Flow
    user: User

    def __init__(self, flow: Flow, user: User) -> None:
        self.flow = flow
        self.user = user

    def get_flow_policies(self, parent_elements: list[DiagramElement]) -> list[DiagramElement]:
        """Collect all policies bound to the flow"""
        elements = []
        for p_index, policy_binding in enumerate(
            get_objects_for_user(self.user, "authentik_policies.view_policybinding")
            .filter(target=self.flow)
            .exclude(policy__isnull=True)
            .order_by("order")
        ):
            element = DiagramElement(
                f"flow_policy_{p_index}",
                _("Policy (%(type)s)" % {"type": policy_binding.policy._meta.verbose_name})
                + "\n"
                + policy_binding.policy.name,
                _("Binding %(order)d" % {"order": policy_binding.order}),
                parent_elements,
            )
            elements.append(element)
        return elements

    def get_stage_policies(
        self,
        stage_index: int,
        stage_binding: FlowStageBinding,
        parent_elements: list[DiagramElement],
    ) -> list[DiagramElement]:
        """First all policies bound to stages since they execute before stages"""
        elements = []
        for p_index, policy_binding in enumerate(
            get_objects_for_user(self.user, "authentik_policies.view_policybinding")
            .filter(target=stage_binding)
            .exclude(policy__isnull=True)
            .order_by("order")
        ):
            elem = DiagramElement(
                f"stage_{stage_index}_policy_{p_index}",
                _("Policy (%(type)s)" % {"type": policy_binding.policy._meta.verbose_name})
                + "\n"
                + policy_binding.policy.name,
                "",
                parent_elements,
            )
            elements.append(elem)
        return elements

    def get_stages(self, parent_elements: list[DiagramElement]) -> list[str | DiagramElement]:
        """Collect all stages"""
        elements = []
        for s_index, stage_binding in enumerate(
            get_objects_for_user(self.user, "authentik_flows.view_flowstagebinding")
            .filter(target=self.flow)
            .order_by("order")
        ):
            stage_policies = self.get_stage_policies(s_index, stage_binding, parent_elements)
            elements.extend(stage_policies)
            element = DiagramElement(
                f"stage_{s_index}",
                _("Stage (%(type)s)" % {"type": stage_binding.stage._meta.verbose_name})
                + "\n"
                + stage_binding.stage.name,
                "",
                stage_policies,
            )
            elements.append(element)

            parent_elements = [element]
        return elements

    def build(self) -> str:
        """Build flowchart"""
        all_elements = [
            "graph TD",
        ]

        pre_flow_policies_element = DiagramElement(
            "flow_pre",
            _("Pre-flow policies"),
        )
        flow_policies = self.get_flow_policies([pre_flow_policies_element])
        if len(flow_policies) > 0:
            all_elements.append(pre_flow_policies_element)
            all_elements.extend(flow_policies)

        flow_element = DiagramElement(
            "flow_start",
            _("Flow") + "\n" + self.flow.name,
            "",
            source=flow_policies,
        )
        all_elements.append(flow_element)

        stages = self.get_stages([flow_element])
        all_elements.extend(stages)

        connections = [x for x in all_elements if isinstance(x, DiagramElement)]

        all_elements.append(
            DiagramElement(
                "done",
                _("End of the flow"),
                "",
                [connections[-1]],
            ),
        )
        return "\n".join([str(x) for x in all_elements])
