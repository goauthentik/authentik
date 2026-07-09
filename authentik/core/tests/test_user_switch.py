"""User switch view tests."""

from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from authentik.core import user_switching
from authentik.core.models import AuthenticatedSession, Session
from authentik.core.tests.utils import (
    create_test_brand,
    create_test_flow,
    create_test_session,
    create_test_user,
)
from authentik.core.user_switching import UserSwitchingSession
from authentik.events.models import Event, EventAction
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
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
from authentik.stages.user_login.models import UserLoginStage


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
        self.brand = create_test_brand(flow_user_switch=self.flow)

    def _post(self, data: dict, query: dict | None = None):
        url = reverse("authentik_api:user-switch")
        if query:
            url = f"{url}?{urlencode(query)}"
        return self.client.post(url, data, format="json")

    def _post_switch(self, user):
        return self._post({"user_pk": user.pk})

    def _assert_redirect(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["redirect"],
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.flow.slug}),
        )

    def _login(self, user) -> str:
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex,
            bindings=[self.login_binding],
            markers=[StageMarker()],
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        return self.client.session.session_key

    def _token(self) -> str:
        token = user_switching._decode_cookie(self.client.cookies[user_switching.COOKIE_NAME].value)
        if token is None:
            self.fail("Expected a user-switching cookie")
        return token

    def test_disabled_brand_rejects_switch_and_add(self):
        self.brand.flow_user_switch = None
        self.brand.save()
        self._login(self.user)
        create_test_session(self.other_user, self._token(), is_current=False)

        for data in ({"user_pk": self.other_user.pk}, {"action": "add"}):
            with self.subTest(data=data):
                response = self._post(data, {"next": "https://example.invalid/"})
                self.assertContains(response, "User switching is disabled.", status_code=400)

    def test_switch_plans_verified_browser_target(self):
        self._login(self.user)
        target = create_test_session(self.other_user, self._token(), is_current=False)

        response = self._post_switch(self.other_user)

        self._assert_redirect(response)
        context = self.client.session[SESSION_KEY_PLAN].context
        self.assertEqual(context[PLAN_CONTEXT_PENDING_USER], self.other_user)
        self.assertEqual(context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER], self.other_user.username)
        self.assertEqual(context[PLAN_CONTEXT_USER_SWITCH_FROM_USER], self.user)
        self.assertEqual(context[PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION], target.session_id)

    def test_add_user_preserves_existing_login(self):
        first_session_key = self._login(self.user)
        response = self._post({"action": "add"})
        self._assert_redirect(response)
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
        first_session_key = self._login(self.user)
        target = create_test_session(self.other_user, self._token(), is_current=False)
        self._assert_redirect(self._post_switch(self.other_user))
        target.session.delete()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(response, self.flow, component="ak-stage-access-denied")
        switching_session = UserSwitchingSession.objects.get(token=self._token())
        self.assertEqual(switching_session.current_session_id, first_session_key)

    def test_switch_flow_policy_applies_to_source_user(self):
        self._login(self.user)
        create_test_session(self.other_user, self._token(), is_current=False)
        PolicyBinding.objects.create(target=self.flow, user=self.other_user, order=0)

        response = self._post_switch(self.other_user)

        self.assertEqual(response.status_code, 404)

    def test_switch_requires_target_from_same_browser(self):
        self._login(self.user)
        create_test_session(self.other_user, "A" * user_switching.TOKEN_LENGTH)

        response = self._post_switch(self.other_user)

        self.assertEqual(response.status_code, 404)

    def test_user_me_lists_live_browser_sessions(self):
        self._login(self.user)
        token = self._token()
        create_test_session(self.other_user, token, is_current=False)
        expired = create_test_session(create_test_user(), token, is_current=False)
        expired.session.expires = timezone.now() - timedelta(seconds=1)
        expired.session.save(update_fields=["expires"])

        response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(
            [(user["username"], user["is_current"]) for user in response.json()["users"]],
            [(self.user.username, True), (self.other_user.username, False)],
        )

    def test_full_switch_replaces_target_and_supersedes_source(self):
        source_session_key = self._login(self.user)
        target = create_test_session(self.other_user, self._token(), is_current=False)

        self._assert_redirect(self._post_switch(self.other_user))
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
