"""Required-action login, completion, and request restrictions."""

from unittest.mock import patch

from django.contrib.messages import get_messages
from django.core.cache import cache
from django.urls import reverse

from authentik.core.models import (
    AuthenticatedSession,
    User,
)
from authentik.core.tests.test_user_switch import _login_through_flow
from authentik.core.tests.utils import create_test_brand, create_test_flow, create_test_user
from authentik.enterprise.license import CACHE_KEY_ENTERPRISE_LICENSE
from authentik.enterprise.next_actions import USER_ATTRIBUTE_NEXT_ACTIONS
from authentik.enterprise.next_actions.flows import (
    SESSION_KEY_PENDING_NEXT_ACTIONS,
    NextActionDoneStageView,
    resolve_next_actions,
)
from authentik.enterprise.tests import enterprise_test, expiry_expired
from authentik.events.models import Event, EventAction
from authentik.events.utils import get_user
from authentik.flows.markers import StageMarker
from authentik.flows.models import (
    Flow,
    FlowAuthenticationRequirement,
    FlowDesignation,
    FlowStageBinding,
    in_memory_stage,
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, PLAN_CONTEXT_REDIRECT, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.dummy.models import DummyStage
from authentik.stages.redirect.models import RedirectMode, RedirectStage
from authentik.stages.user_login.models import UserLoginStage


class TestUserLoginNextActions(FlowTestCase):
    """Next action enforcement tests"""

    def setUp(self):
        super().setUp()
        cache.delete(CACHE_KEY_ENTERPRISE_LICENSE)
        self.user = create_test_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = UserLoginStage.objects.create(name=generate_id())
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)
        self.executor_url = reverse(
            "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
        )

    def create_action_flow(self) -> Flow:
        """Stage configuration flow with a single dummy stage, requiring authentication
        like the built-in configuration flows"""
        flow = create_test_flow(
            FlowDesignation.STAGE_CONFIGURATION,
            authentication=FlowAuthenticationRequirement.REQUIRE_AUTHENTICATED,
        )
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
        )
        return flow

    def test_resolve_actions_preserves_order_in_one_query(self):
        first = self.create_action_flow()
        second = self.create_action_flow()
        with self.assertNumQueries(1):
            self.assertEqual(
                resolve_next_actions([second.slug, first.slug, second.slug]),
                [second, first, second],
            )

    def set_next_actions(self, value):
        self.user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS] = value
        self.user.save()

    def start_login(self):
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        return self.client.get(self.executor_url)

    def begin_actions(self, destination: str, action: Flow) -> str:
        """Visit a blocked destination and return the action executor URL."""
        response = self.client.get(destination, HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": action.slug}),
        )
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.flow_pk, action.pk.hex)
        self.assertEqual(plan.context[PLAN_CONTEXT_REDIRECT], destination)
        return reverse("authentik_api:flow-executor", kwargs={"flow_slug": action.slug})

    def complete_action(self, executor_url: str, action: Flow):
        """Complete the action's dummy stage and its in-memory completion stage."""
        response = self.client.get(executor_url)
        self.assertStageResponse(response, action, component="ak-stage-dummy")
        response = self.client.post(executor_url, {})
        self.assertEqual(response.status_code, 302)
        return self.client.get(executor_url)

    @enterprise_test()
    def test_login_flags_session_and_blocks_oauth(self):
        """A completed login cannot continue an OAuth authorization before its actions."""
        action = self.create_action_flow()
        self.set_next_actions([action.slug])

        response = self.start_login()
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(AuthenticatedSession.objects.filter(user=self.user).exists())
        self.assertTrue(self.client.session[SESSION_KEY_PENDING_NEXT_ACTIONS])
        self.assertIn(
            "Login successful. Complete the required actions before continuing.",
            [str(message) for message in get_messages(response.wsgi_request)],
        )

        authorize = reverse("authentik_providers_oauth2:authorize")
        response = self.client.get(authorize, HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": action.slug}),
        )
        self.assertEqual(
            [str(message) for message in get_messages(response.wsgi_request)],
            ["Login successful. Complete the required actions before continuing."],
        )

    @enterprise_test()
    def test_adding_account_enforces_next_actions(self):
        create_test_brand(flow_authentication=self.flow, flow_user_switch=self.flow)
        _login_through_flow(self.client, self.flow, self.binding, create_test_user())
        action = self.create_action_flow()
        self.set_next_actions([action.slug])
        response = self.client.post(
            reverse("authentik_api:user-switch"), {"action": "add"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        session[SESSION_KEY_PLAN].context[PLAN_CONTEXT_PENDING_USER] = self.user
        session.save()
        self.client.get(self.executor_url)
        self.assertTrue(self.client.session[SESSION_KEY_PENDING_NEXT_ACTIONS])
        self.assertEqual(
            self.client.get(reverse("authentik_api:application-list")).status_code, 403
        )

    @enterprise_test()
    def test_action_completion_clears_session(self):
        """Completing the last action removes both the user attribute and session flag."""
        action = self.create_action_flow()
        self.set_next_actions([action.slug])

        self.start_login()
        destination = reverse("authentik_core:if-user")
        executor_url = self.begin_actions(destination, action)
        response = self.complete_action(executor_url, action)
        self.assertStageRedirects(response, destination)

        self.user.refresh_from_db()
        self.assertNotIn(USER_ATTRIBUTE_NEXT_ACTIONS, self.user.attributes)
        self.assertNotIn(SESSION_KEY_PENDING_NEXT_ACTIONS, self.client.session)
        event = Event.objects.filter(action=EventAction.NEXT_ACTION_COMPLETED).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["flow_slug"], action.slug)
        self.assertEqual(event.user, get_user(self.user))
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.MODEL_UPDATED,
                context__model__model_name="user",
            ).exists()
        )

    @enterprise_test()
    def test_direct_action_entry_completes(self):
        """Entering the executor directly still records required-action completion."""
        action = self.create_action_flow()
        self.set_next_actions([action.slug])
        self.start_login()
        executor_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": action.slug})
        self.complete_action(executor_url, action)
        self.user.refresh_from_db()
        self.assertNotIn(USER_ATTRIBUTE_NEXT_ACTIONS, self.user.attributes)
        self.assertNotIn(SESSION_KEY_PENDING_NEXT_ACTIONS, self.client.session)

    @enterprise_test()
    def test_browser_navigation_preserves_action_progress(self):
        """Revisiting a blocked page must not restart an action in progress."""
        action = self.create_action_flow()
        self.set_next_actions([action.slug])
        self.start_login()
        destination = reverse("authentik_core:if-user")
        executor_url = self.begin_actions(destination, action)
        self.client.get(executor_url)
        self.client.post(executor_url, {})
        self.begin_actions(destination, action)
        self.assertStageRedirects(self.client.get(executor_url), destination)
        self.user.refresh_from_db()
        self.assertNotIn(USER_ATTRIBUTE_NEXT_ACTIONS, self.user.attributes)

    @enterprise_test()
    def test_completion_preserves_updates_since_authentication(self):
        """An update after authentication must survive action completion."""
        action = self.create_action_flow()
        self.set_next_actions([action.slug])
        self.start_login()
        executor_url = self.begin_actions(reverse("authentik_core:if-user"), action)
        dispatch = NextActionDoneStageView.dispatch

        def update_then_complete(view, request):
            user = User.objects.get(pk=self.user.pk)
            user.attributes["updated"] = "preserved"
            user.save(update_fields=["attributes"])
            return dispatch(view, request)

        with patch.object(NextActionDoneStageView, "dispatch", update_then_complete):
            self.complete_action(executor_url, action)
        self.user.refresh_from_db()
        self.assertEqual(self.user.attributes.get("updated"), "preserved")
        self.assertNotIn(USER_ATTRIBUTE_NEXT_ACTIONS, self.user.attributes)

    @enterprise_test()
    def test_action_redirect_keeps_completion(self):
        """Flow handoffs retain completion and the original destination."""
        for keep_context, redirects in ((True, 1), (False, 1), (True, 2), (False, 2)):
            with self.subTest(keep_context=keep_context, redirects=redirects):
                self.client.logout()
                target = self.create_action_flow()
                chain = [target]
                for _ in range(redirects):
                    action = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
                    FlowStageBinding.objects.create(
                        target=action,
                        stage=RedirectStage.objects.create(
                            name=generate_id(),
                            mode=RedirectMode.FLOW,
                            target_flow=chain[-1],
                            keep_context=keep_context,
                        ),
                        order=0,
                    )
                    chain.append(action)
                self.set_next_actions([action.slug])
                self.start_login()
                destination = reverse("authentik_core:if-user")
                executor_url = self.begin_actions(destination, action)
                for redirected in reversed(chain[:-1]):
                    target_url = reverse(
                        "authentik_core:if-flow", kwargs={"flow_slug": redirected.slug}
                    )
                    self.assertStageRedirects(self.client.get(executor_url), target_url)
                    self.assertEqual(self.client.get(target_url).status_code, 200)
                    executor_url = reverse(
                        "authentik_api:flow-executor", kwargs={"flow_slug": redirected.slug}
                    )
                self.assertStageRedirects(self.complete_action(executor_url, target), destination)
                self.user.refresh_from_db()
                self.assertNotIn(USER_ATTRIBUTE_NEXT_ACTIONS, self.user.attributes)
                self.assertNotIn(SESSION_KEY_PENDING_NEXT_ACTIONS, self.client.session)

    @enterprise_test()
    def test_action_cannot_redirect_to_login_or_logout(self):
        for designation in (FlowDesignation.AUTHENTICATION, FlowDesignation.INVALIDATION):
            with self.subTest(designation=designation):
                self.client.logout()
                action = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
                FlowStageBinding.objects.create(
                    target=action,
                    stage=RedirectStage.objects.create(
                        name=generate_id(),
                        mode=RedirectMode.FLOW,
                        target_flow=create_test_flow(designation),
                    ),
                    order=0,
                )
                self.set_next_actions([action.slug])
                self.start_login()
                executor_url = self.begin_actions(reverse("authentik_core:if-user"), action)
                self.assertStageResponse(
                    self.client.get(executor_url), component="ak-stage-access-denied"
                )
                self.assertTrue(self.client.session[SESSION_KEY_PENDING_NEXT_ACTIONS])
                self.user.refresh_from_db()
                self.assertEqual(self.user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS], [action.slug])

    @enterprise_test()
    def test_action_as_string(self):
        """A single flow slug works without being wrapped in a list"""
        action = self.create_action_flow()
        self.set_next_actions(action.slug)

        self.start_login()
        destination = reverse("authentik_core:if-user")
        executor_url = self.begin_actions(destination, action)
        self.complete_action(executor_url, action)

        self.user.refresh_from_db()
        self.assertNotIn(USER_ATTRIBUTE_NEXT_ACTIONS, self.user.attributes)

    @enterprise_test()
    def test_multiple_actions(self):
        """Multiple actions run in order and are cleared one by one"""
        first = self.create_action_flow()
        second = self.create_action_flow()
        self.set_next_actions([first.slug, second.slug])

        self.start_login()
        destination = reverse("authentik_core:if-user")
        executor_url = self.begin_actions(destination, first)
        self.complete_action(executor_url, first)
        self.user.refresh_from_db()
        self.assertEqual(self.user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS], [second.slug])

        executor_url = self.begin_actions(destination, second)
        response = self.complete_action(executor_url, second)
        self.assertStageRedirects(response, destination)

        self.user.refresh_from_db()
        self.assertNotIn(USER_ATTRIBUTE_NEXT_ACTIONS, self.user.attributes)

    @enterprise_test()
    def test_invalid_action_keeps_session_blocked(self):
        """A broken action cannot turn a restricted session into an unrestricted one."""
        self.set_next_actions(["does-not-exist"])

        self.start_login()
        response = self.client.get(reverse("authentik_core:if-user"), HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.session[SESSION_KEY_PENDING_NEXT_ACTIONS])

    @enterprise_test()
    def test_malformed_actions_fail_closed(self):
        """False-like invalid values are not an empty action list."""
        for value in (None, False, 0, "", {}):
            with self.subTest(value=value):
                self.client.logout()
                self.set_next_actions(value)
                self.start_login()
                response = self.client.get(
                    reverse("authentik_core:if-user"), HTTP_ACCEPT="text/html"
                )
                self.assertEqual(response.status_code, 403)
                self.assertTrue(self.client.session[SESSION_KEY_PENDING_NEXT_ACTIONS])

    @enterprise_test()
    def test_non_applicable_action_keeps_session_blocked(self):
        """A denied action cannot turn a restricted session into an unrestricted one."""
        action = self.create_action_flow()
        PolicyBinding.objects.create(
            policy=DummyPolicy.objects.create(
                name=generate_id(), result=False, wait_min=0, wait_max=1
            ),
            target=action,
            order=0,
        )
        self.set_next_actions([action.slug])

        self.start_login()
        response = self.client.get(reverse("authentik_core:if-user"), HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.session[SESSION_KEY_PENDING_NEXT_ACTIONS])

    @enterprise_test(expiry=expiry_expired)
    def test_expired_license_still_enforces(self):
        """An expired license does not switch off next actions"""
        action = self.create_action_flow()
        self.set_next_actions([action.slug])

        self.start_login()
        self.assertTrue(self.client.session[SESSION_KEY_PENDING_NEXT_ACTIONS])
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"), HTTP_ACCEPT="text/html"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": action.slug}),
        )

    def test_without_license_actions_are_skipped(self):
        """Without an enterprise license the login proceeds without actions"""
        action = self.create_action_flow()
        self.set_next_actions([action.slug])

        response = self.start_login()
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS], [action.slug])
        self.assertTrue(AuthenticatedSession.objects.filter(user=self.user).exists())
        self.assertNotIn(SESSION_KEY_PENDING_NEXT_ACTIONS, self.client.session)


class TestPendingNextActionsMiddleware(FlowTestCase):
    """Tests for requests made by a session flagged during login."""

    def setUp(self):
        super().setUp()
        cache.delete(CACHE_KEY_ENTERPRISE_LICENSE)
        self.user = create_test_user()
        self.action = create_test_flow(
            FlowDesignation.STAGE_CONFIGURATION,
            authentication=FlowAuthenticationRequirement.REQUIRE_AUTHENTICATED,
        )
        FlowStageBinding.objects.create(
            target=self.action, stage=DummyStage.objects.create(name=generate_id()), order=0
        )
        self.user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS] = [self.action.slug]
        self.user.save()
        self.client.force_login(self.user)
        session = self.client.session
        session[SESSION_KEY_PENDING_NEXT_ACTIONS] = True
        session.save()

    def test_api_request_denied(self):
        """A non-HTML request is denied instead of redirected"""
        response = self.client.get(
            reverse("authentik_api:application-list"), HTTP_ACCEPT="application/json"
        )
        self.assertEqual(response.status_code, 403)

    def test_pending_user_cannot_remove_their_actions(self):
        """A restricted session cannot use its edit permission to release itself."""
        self.user.assign_perms_to_managed_role("authentik_core.view_user")
        self.user.assign_perms_to_managed_role("authentik_core.change_user", self.user)
        response = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
            {"attributes": {}},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS], [self.action.slug])

    def test_user_info_stays_available(self):
        """Required flows can read user info with or without a deployment prefix."""
        for prefix in ("", "/authentik"):
            with self.subTest(prefix=prefix):
                response = self.client.get(reverse("authentik_api:user-me"), SCRIPT_NAME=prefix)
                self.assertEqual(response.status_code, 200)

    def test_unrelated_flow_api_is_denied(self):
        """The runtime allowlist does not expose flow administration APIs."""
        response = self.client.get(
            reverse("authentik_api:flow-list"), HTTP_ACCEPT="application/json"
        )
        self.assertEqual(response.status_code, 403)

    def test_other_flow_is_redirected_to_action(self):
        """A restricted session cannot start a different flow."""
        other = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        response = self.client.get(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": other.slug}),
            HTTP_ACCEPT="text/html",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.action.slug}),
        )

    def test_stale_completion_cannot_authorize_another_flow(self):
        other = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        plan = FlowPlan(flow_pk=other.pk.hex)
        plan.append_stage(in_memory_stage(NextActionDoneStageView, flow_slug="removed-action"))
        self.set_flow_plan(plan)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": other.slug})
        )
        self.assertEqual(response.status_code, 403)

    def test_logout_stays_available(self):
        """A restricted session can still start the logout flow."""
        Flow.objects.filter(designation=FlowDesignation.INVALIDATION).delete()
        invalidation = create_test_flow(FlowDesignation.INVALIDATION)
        response = self.client.get(reverse("authentik_flows:default-invalidation"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": invalidation.slug}),
        )
        self.assertTrue(self.client.session[SESSION_KEY_PENDING_NEXT_ACTIONS])

    def test_no_pending_actions_pass(self):
        """Removing the actions releases a flagged session."""
        self.user.attributes.pop(USER_ATTRIBUTE_NEXT_ACTIONS)
        self.user.save()
        response = self.client.get(reverse("authentik_core:if-user"), HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY_PENDING_NEXT_ACTIONS, self.client.session)

    def test_existing_session_is_not_retroactively_flagged(self):
        """The attribute applies on the next login, not to sessions already in progress."""
        session = self.client.session
        session.pop(SESSION_KEY_PENDING_NEXT_ACTIONS)
        session.save()
        response = self.client.get(reverse("authentik_core:if-user"), HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 200)
