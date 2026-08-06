"""Next action flows, required before a user can log in"""

from typing import Any

from authentik.flows.models import Flow, FlowDesignation

# Flows that create or end a session cannot run as a next action inside a login
NEXT_ACTION_DISALLOWED_DESIGNATIONS = [
    FlowDesignation.AUTHENTICATION,
    FlowDesignation.INVALIDATION,
]


def resolve_next_actions(value: Any) -> list[Flow]:
    """Resolve the value of the next-actions user attribute (a flow slug or
    a list of flow slugs) to flows. Raises ValueError for entries that don't
    resolve to a usable flow."""
    slugs = value if isinstance(value, list) else [value]
    flows = []
    for slug in slugs:
        if not isinstance(slug, str):
            raise ValueError(f"Invalid next action entry: {slug!r}")
        flow = Flow.objects.filter(slug=slug).first()
        if not flow:
            raise ValueError(f"Next action flow does not exist: {slug}")
        if flow.designation in NEXT_ACTION_DISALLOWED_DESIGNATIONS:
            raise ValueError(f"Flow cannot be used as a next action: {slug}")
        flows.append(flow)
    return flows
