"""Flows Diagram API"""
from dataclasses import dataclass, field
from typing import Optional

from django.utils.translation import gettext as _
from guardian.shortcuts import get_objects_for_user
from rest_framework.serializers import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.flows.models import Flow, FlowAuthenticationRequirement, FlowStageBinding


@dataclass
class DiagramElement:
    """Single element used in a diagram"""

    identifier: str
    description: str
    action: Optional[str] = None
    source: Optional[list["DiagramElement"]] = None

    style: list[str] = field(default_factory=lambda: ["[", "]"])

    def __str__(self) -> str:
        description = self.description.replace('"', "#quot;")
        element = f'{self.identifier}{self.style[0]}"{description}"{self.style[1]}'
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
                style=["{{", "}}"],
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
            element = DiagramElement(
                f"stage_{stage_index}_policy_{p_index}",
                _("Policy (%(type)s)" % {"type": policy_binding.policy._meta.verbose_name})
                + "\n"
                + policy_binding.policy.name,
                "",
                parent_elements,
                style=["{{", "}}"],
            )
            elements.append(element)
        return elements

    def get_stages(self, parent_elements: list[DiagramElement]) -> list[str | DiagramElement]:
        """Collect all stages"""
        elements = []
        stages = []
        for s_index, stage_binding in enumerate(
            get_objects_for_user(self.user, "authentik_flows.view_flowstagebinding")
            .filter(target=self.flow)
            .order_by("order")
        ):
            stage_policies = self.get_stage_policies(s_index, stage_binding, parent_elements)
            elements.extend(stage_policies)

            action = ""
            if len(stage_policies) > 0:
                action = _("Policy passed")

            element = DiagramElement(
                f"stage_{s_index}",
                _("Stage (%(type)s)" % {"type": stage_binding.stage._meta.verbose_name})
                + "\n"
                + stage_binding.stage.name,
                action,
                stage_policies,
                style=["([", "])"],
            )
            stages.append(element)

            parent_elements = [element]

            # This adds connections for policy denies, but retroactively, as we can't really
            # look ahead
            # Check if we have a stage behind us and if it has any sources
            if s_index > 0:
                last_stage: DiagramElement = stages[s_index - 1]
                if last_stage.source and len(last_stage.source) > 0:
                    # If it has any sources, add a connection from each of that stage's sources
                    # to this stage
                    for source in last_stage.source:
                        elements.append(
                            DiagramElement(
                                element.identifier,
                                element.description,
                                _("Policy denied"),
                                [source],
                                style=element.style,
                            )
                        )

        if len(stages) > 0:
            elements.append(
                DiagramElement(
                    "done",
                    _("End of the flow"),
                    "",
                    [stages[-1]],
                    style=["[[", "]]"],
                ),
            )
        return stages + elements

    def get_flow_auth_requirement(self) -> list[DiagramElement]:
        """Get flow authentication requirement"""
        end_el = DiagramElement(
            "done",
            _("End of the flow"),
            _("Requirement not fulfilled"),
            style=["[[", "]]"],
        )
        elements = []
        if self.flow.authentication == FlowAuthenticationRequirement.NONE:
            return []
        auth = DiagramElement(
            "flow_auth_requirement",
            _("Flow authentication requirement") + "\n" + self.flow.authentication,
        )
        elements.append(auth)
        end_el.source = [auth]
        elements.append(end_el)
        elements.append(
            DiagramElement("flow_start", "placeholder", _("Requirement fulfilled"), source=[auth])
        )
        return elements

    def build(self) -> str:
        """Build flowchart"""
        all_elements = [
            "graph TD",
        ]

        all_elements.extend(self.get_flow_auth_requirement())

        pre_flow_policies_element = DiagramElement(
            "flow_pre", _("Pre-flow policies"), style=["[[", "]]"]
        )
        flow_policies = self.get_flow_policies([pre_flow_policies_element])
        if len(flow_policies) > 0:
            all_elements.append(pre_flow_policies_element)
            all_elements.extend(flow_policies)
            all_elements.append(
                DiagramElement(
                    "done",
                    _("End of the flow"),
                    _("Policy denied"),
                    flow_policies,
                    style=["[[", "]]"],
                )
            )

        flow_element = DiagramElement(
            "flow_start",
            _("Flow") + "\n" + self.flow.name,
            "" if len(flow_policies) > 0 else None,
            source=flow_policies,
            style=["[[", "]]"],
        )
        all_elements.append(flow_element)

        stages = self.get_stages([flow_element])
        all_elements.extend(stages)
        if len(stages) < 1:
            all_elements.append(
                DiagramElement(
                    "done",
                    _("End of the flow"),
                    "",
                    [flow_element],
                    style=["[[", "]]"],
                ),
            )
        return "\n".join([str(x) for x in all_elements])
