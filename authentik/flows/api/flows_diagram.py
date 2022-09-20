"""Flows Diagram API"""
from dataclasses import dataclass

from django.utils.translation import gettext as _
from guardian.shortcuts import get_objects_for_user
from rest_framework.serializers import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.flows.models import Flow


@dataclass
class DiagramElement:
    """Single element used in a diagram"""

    identifier: str
    type: str
    rest: str

    def __str__(self) -> str:
        return f"{self.identifier}=>{self.type}: {self.rest}"


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

    def build(self) -> str:
        """Build flowchart"""
        header = [
            DiagramElement("st", "start", "Start"),
        ]
        body: list[DiagramElement] = []
        footer = []
        # Collect all elements we need
        # First, policies bound to the flow itself
        for p_index, policy_binding in enumerate(
            get_objects_for_user(self.user, "authentik_policies.view_policybinding")
            .filter(target=self.flow)
            .exclude(policy__isnull=True)
            .order_by("order")
        ):
            body.append(
                DiagramElement(
                    f"flow_policy_{p_index}",
                    "condition",
                    _("Policy (%(type)s)" % {"type": policy_binding.policy._meta.verbose_name})
                    + "\n"
                    + policy_binding.policy.name,
                )
            )
        # Collect all stages
        for s_index, stage_binding in enumerate(
            get_objects_for_user(self.user, "authentik_flows.view_flowstagebinding")
            .filter(target=self.flow)
            .order_by("order")
        ):
            # First all policies bound to stages since they execute before stages
            for p_index, policy_binding in enumerate(
                get_objects_for_user(self.user, "authentik_policies.view_policybinding")
                .filter(target=stage_binding)
                .exclude(policy__isnull=True)
                .order_by("order")
            ):
                body.append(
                    DiagramElement(
                        f"stage_{s_index}_policy_{p_index}",
                        "condition",
                        _("Policy (%(type)s)" % {"type": policy_binding.policy._meta.verbose_name})
                        + "\n"
                        + policy_binding.policy.name,
                    )
                )
            body.append(
                DiagramElement(
                    f"stage_{s_index}",
                    "operation",
                    _("Stage (%(type)s)" % {"type": stage_binding.stage._meta.verbose_name})
                    + "\n"
                    + stage_binding.stage.name,
                )
            )
        # If the 2nd last element is a policy, we need to have an item to point to
        # for a negative case
        body.append(
            DiagramElement("e", "end", "End|future"),
        )
        if len(body) == 1:
            footer.append("st(right)->e")
        else:
            # Actual diagram flow
            footer.append(f"st(right)->{body[0].identifier}")
            for index in range(len(body) - 1):
                element: DiagramElement = body[index]
                if element.type == "condition":
                    # Policy passes, link policy yes to next stage
                    footer.append(f"{element.identifier}(yes, right)->{body[index + 1].identifier}")
                    # For policies bound to the flow itself, if they deny,
                    # the flow doesn't get executed, hence directly to the end
                    if element.identifier.startswith("flow_policy_"):
                        footer.append(f"{element.identifier}(no, bottom)->e")
                    else:
                        # Policy doesn't pass, go to stage after next stage
                        no_element = body[index + 1]
                        if no_element.type != "end":
                            no_element = body[index + 2]
                        footer.append(f"{element.identifier}(no, bottom)->{no_element.identifier}")
                elif element.type == "operation":
                    footer.append(f"{element.identifier}(bottom)->{body[index + 1].identifier}")
        return "\n".join([str(x) for x in header + body + footer])
