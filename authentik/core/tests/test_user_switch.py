"""User switch view tests."""

from datetime import timedelta
from typing import cast

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from authentik.core import user_switching
from authentik.core.models import AuthenticatedSession, Session, User, UserSwitchingSession
from authentik.core.tests.utils import (
    create_test_brand,
    create_test_flow,
    create_test_session,
    create_test_user,
)
from authentik.events.models import Event, EventAction
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_USER_SWITCH_ADD_USER,
    PLAN_CONTEXT_USER_SWITCH_FROM_USER,
    PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION,
    FlowPlan,
)
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.policies.models import PolicyBinding
from authentik.policies.types import PolicyRequest
from authentik.stages.user_login.models import UserLoginStage


def post_user_switch(
    client: APIClient,
    data: dict[str, object],
    query: dict[str, str] | None = None,
) -> Response:
    """Post to the user switch endpoint."""
    url = reverse("authentik_api:user-switch")
    if query:
        url = f"{url}?{urlencode(query)}"
    return cast(Response, client.post(url, data, format="json"))


def assert_switch_redirect(response: Response, flow: Flow) -> None:
    """Assert that a user switch starts the configured flow."""
    if response.status_code != status.HTTP_200_OK:
        raise AssertionError(f"Expected status 200, got {response.status_code}")
    expected_redirect = reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
    if response.data["redirect"] != expected_redirect:
        raise AssertionError(
            f"Expected redirect {expected_redirect!r}, got {response.data['redirect']!r}"
        )


def login_through_flow(
    client: APIClient,
    flow: Flow,
    login_binding: FlowStageBinding,
    user: User,
) -> str:
    """Log the test client in through the flow executor."""
    plan = FlowPlan(
        flow_pk=flow.pk.hex,
        bindings=[login_binding],
        markers=[StageMarker()],
    )
    plan.context[PLAN_CONTEXT_PENDING_USER] = user
    session = client.session
    session[SESSION_KEY_PLAN] = plan
    session.save()
    response = client.get(reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}))
    if response.status_code != status.HTTP_200_OK:
        raise AssertionError(f"Expected status 200, got {response.status_code}")
    session_key = client.session.session_key
    if session_key is None:
        raise AssertionError("Expected the logged-in client to have a session key")
    return session_key


def get_switching_token(client: APIClient) -> str:
    """Return the user-switching token from the test client."""
    token = user_switching.decode_cookie(client.cookies[user_switching.COOKIE_NAME].value)
    if token is None:
        raise AssertionError("Expected a user-switching cookie")
    return token


class TestUserSwitch(FlowTestCase):
    """Test starting and completing the brand's user switch flow."""

    def setUp(self):
        super().setUp()
        self.user = create_test_user()
        self.other_user = create_test_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.login_binding = FlowStageBinding.objects.create(
            target=self.flow,
            stage=UserLoginStage.objects.create(name="login"),
            order=0,
        )
        self.brand = create_test_brand(flow_authentication=self.flow, flow_user_switch=self.flow)

    def test_disabled_brand_rejects_switch_and_add(self):
        self.brand.flow_user_switch = None
        self.brand.save()
        login_through_flow(self.client, self.flow, self.login_binding, self.user)
        create_test_session(self.other_user, get_switching_token(self.client), is_current=False)

        for data in ({"user_pk": self.other_user.pk}, {"action": "add"}):
            with self.subTest(data=data):
                response = post_user_switch(self.client, data, {"next": "https://example.invalid/"})
                self.assertContains(response, "User switching is disabled.", status_code=400)

    def test_low_permission_user_can_switch_verified_browser_target(self):
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(self.user.get_all_permissions(), set())
        login_through_flow(self.client, self.flow, self.login_binding, self.user)
        target = create_test_session(
            self.other_user, get_switching_token(self.client), is_current=False
        )

        response = post_user_switch(self.client, {"user_pk": self.other_user.pk})

        assert_switch_redirect(response, self.flow)
        context = self.client.session[SESSION_KEY_PLAN].context
        self.assertEqual(context[PLAN_CONTEXT_PENDING_USER], self.other_user)
        self.assertEqual(context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER], self.other_user.username)
        self.assertEqual(context[PLAN_CONTEXT_USER_SWITCH_FROM_USER], self.user)
        self.assertEqual(context[PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION], target.session_id)

    def test_add_user_preserves_existing_login(self):
        first_session_key = login_through_flow(
            self.client, self.flow, self.login_binding, self.user
        )
        response = post_user_switch(self.client, {"action": "add"})
        assert_switch_redirect(response, self.flow)
        plan = self.client.session[SESSION_KEY_PLAN]
        self.assertTrue(plan.context[PLAN_CONTEXT_USER_SWITCH_ADD_USER])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.other_user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertNotEqual(self.client.session.session_key, first_session_key)
        self.assertTrue(Session.objects.filter(session_key=first_session_key).exists())

    def test_target_is_revalidated_before_login(self):
        first_session_key = login_through_flow(
            self.client, self.flow, self.login_binding, self.user
        )
        target = create_test_session(
            self.other_user, get_switching_token(self.client), is_current=False
        )
        assert_switch_redirect(
            post_user_switch(self.client, {"user_pk": self.other_user.pk}), self.flow
        )
        target.session.delete()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="The selected session is no longer available. Please try again.",
        )
        switching_session = UserSwitchingSession.objects.get(token=get_switching_token(self.client))
        self.assertEqual(switching_session.current_session_id, first_session_key)

    def test_switch_flow_policy_applies_to_source_user(self):
        login_through_flow(self.client, self.flow, self.login_binding, self.user)
        create_test_session(self.other_user, get_switching_token(self.client), is_current=False)
        PolicyBinding.objects.create(target=self.flow, user=self.other_user, order=0)

        response = post_user_switch(self.client, {"user_pk": self.other_user.pk})

        self.assertEqual(response.status_code, 404)

    def test_switch_requires_target_from_same_browser(self):
        login_through_flow(self.client, self.flow, self.login_binding, self.user)
        create_test_session(self.other_user, "A" * user_switching.TOKEN_LENGTH)

        response = post_user_switch(self.client, {"user_pk": self.other_user.pk})

        self.assertEqual(response.status_code, 404)

    def test_user_me_lists_live_browser_sessions(self):
        login_through_flow(self.client, self.flow, self.login_binding, self.user)
        token = get_switching_token(self.client)
        create_test_session(self.other_user, token, is_current=False)
        expired = create_test_session(create_test_user(), token, is_current=False)
        expired.session.expires = timezone.now() - timedelta(seconds=1)
        expired.session.save(update_fields=["expires"])

        response = self.client.get(reverse("authentik_api:user-me"))

        body = response.json()
        self.assertTrue(body["user"]["is_current"])
        self.assertEqual(
            [(user["username"], user["is_current"]) for user in body["users"]],
            [(self.other_user.username, False)],
        )

    def test_recent_user_switch_target(self):
        login_through_flow(self.client, self.flow, self.login_binding, self.user)
        target = create_test_session(
            self.other_user, get_switching_token(self.client), is_current=False
        )
        http_request = self.client.get(reverse("authentik_api:user-me")).wsgi_request
        policy_request = PolicyRequest(self.user)
        policy_request.http_request = http_request
        policy_request.context.update(
            {
                PLAN_CONTEXT_PENDING_USER: self.other_user,
                PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION: target.session_id,
            }
        )

        self.assertTrue(
            user_switching.is_user_switch_target_recent(policy_request, timedelta(hours=24))
        )
        Session.objects.filter(pk=target.session_id).update(
            last_used=timezone.now() - timedelta(days=2)
        )
        self.assertFalse(
            user_switching.is_user_switch_target_recent(policy_request, timedelta(hours=24))
        )

    def test_full_switch_replaces_target_and_supersedes_source(self):
        source_session_key = login_through_flow(
            self.client, self.flow, self.login_binding, self.user
        )
        target = create_test_session(
            self.other_user, get_switching_token(self.client), is_current=False
        )

        assert_switch_redirect(
            post_user_switch(self.client, {"user_pk": self.other_user.pk}), self.flow
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        current_session_key = self.client.session.session_key
        self.assertNotEqual(current_session_key, source_session_key)
        self.assertEqual(
            AuthenticatedSession.objects.get(session_id=current_session_key).user,
            self.other_user,
        )
        self.assertFalse(Session.objects.filter(session_key=target.session_id).exists())
        self.assertTrue(Session.objects.filter(session_key=source_session_key).exists())
        event = Event.objects.filter(action=EventAction.LOGIN, context__is_user_switch=True).get()
        self.assertEqual(event.user["username"], self.other_user.username)
        self.assertEqual(
            event.context[PLAN_CONTEXT_USER_SWITCH_FROM_USER]["username"],
            self.user.username,
        )

        self.client.cookies[settings.SESSION_COOKIE_NAME] = source_session_key
        self.assertEqual(
            self.client.get(reverse("authentik_api:user-me")).status_code,
            403,
        )
