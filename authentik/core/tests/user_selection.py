"""Test helpers for browser session selection."""

from django.utils.crypto import get_random_string

from authentik.core.models import AuthenticatedSession, Session, User
from authentik.core.sessions import SessionStore
from authentik.core.tests.utils import create_test_brand, create_test_flow
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.root.middleware import BROWSER_KEY_LENGTH, COOKIE_NAME_BROWSER
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


def set_browser_key(test_case) -> str:
    """Give the test client a browser cookie, returning its value."""
    cookie = test_case.client.cookies.get(COOKIE_NAME_BROWSER)
    if cookie and cookie.value:
        return cookie.value
    browser_key = get_random_string(BROWSER_KEY_LENGTH)
    test_case.client.cookies[COOKIE_NAME_BROWSER] = browser_key
    return browser_key


def create_browser_session(test_case, user: User) -> AuthenticatedSession:
    """Create a live login for the given user, bound to the test client's browser cookie."""
    browser_key = set_browser_key(test_case)
    store = SessionStore()
    store.create()
    return AuthenticatedSession.objects.create(
        session=Session.objects.get(session_key=store.session_key),
        user=user,
        browser_key=browser_key,
    )
