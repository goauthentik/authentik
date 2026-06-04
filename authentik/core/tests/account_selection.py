"""Test helpers for browser-local account selection."""

from django.core.signing import dumps

from authentik.core.account_selection import COOKIE_NAME_KNOWN_ACCOUNTS
from authentik.core.models import AuthenticatedSession, Session, User
from authentik.core.tests.utils import create_test_brand, create_test_flow
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.stages.account_selection.models import AccountSelectionStage, AccountSwitchStage


def create_test_account_selection_flow(
    *,
    bind_to_brand: bool = True,
) -> tuple[Flow, AccountSelectionStage, AccountSwitchStage]:
    """Create an account-selection flow with selection and switch stages."""
    flow = create_test_flow(FlowDesignation.ACCOUNT_SELECTION)
    if bind_to_brand:
        brand = create_test_brand()
        brand.flow_account_selection = flow
        brand.save()
    selection_stage = AccountSelectionStage.objects.create(name=generate_id())
    switch_stage = AccountSwitchStage.objects.create(name=generate_id())
    FlowStageBinding.objects.create(target=flow, stage=selection_stage, order=10)
    FlowStageBinding.objects.create(target=flow, stage=switch_stage, order=100)
    return flow, selection_stage, switch_stage


def remember_live_accounts(test_case, *users: User) -> list[dict[str, str]]:
    """Store browser-local accounts backed by live authenticated sessions."""
    accounts = []
    for index, user in enumerate(users):
        client = test_case.client if index == 0 else test_case.client_class()
        client.force_login(user)
        session = Session.objects.get(session_key=client.session.session_key)
        AuthenticatedSession.objects.update_or_create(
            session=session,
            defaults={"user": user},
        )
        accounts.append({"uid": user.uuid.hex, "session": session.session_key})
    test_case.client.cookies[COOKIE_NAME_KNOWN_ACCOUNTS] = dumps(accounts)
    return accounts
