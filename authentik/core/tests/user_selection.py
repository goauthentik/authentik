"""Test helpers for browser-local user selection."""

from django.core.signing import dumps

from authentik.core.models import User
from authentik.core.tests.utils import create_test_brand, create_test_flow
from authentik.core.user_selection import COOKIE_NAME_KNOWN_USERS
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.stages.user_selection.models import UserSelectionStage


def create_test_user_selection_flow(
    *,
    bind_to_brand: bool = True,
) -> tuple[Flow, UserSelectionStage]:
    """Create a user-selection flow with a picker stage."""
    flow = create_test_flow(FlowDesignation.USER_SELECTION)
    if bind_to_brand:
        brand = create_test_brand()
        brand.flow_user_selection = flow
        brand.save()
    selection_stage = UserSelectionStage.objects.create(name=generate_id())
    FlowStageBinding.objects.create(target=flow, stage=selection_stage, order=10)
    return flow, selection_stage


def remember_known_users(test_case, *users: User) -> list[dict[str, str]]:
    """Store browser-local remembered users."""
    payload = [{"uid": user.uuid.hex} for user in users]
    test_case.client.cookies[COOKIE_NAME_KNOWN_USERS] = dumps(payload)
    return payload
