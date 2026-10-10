"""Required action enforcement tests"""

from unittest.mock import patch
from urllib.parse import urlencode

from django.core.cache import cache
from django.urls import reverse

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.enterprise.license import CACHE_KEY_ENTERPRISE_LICENSE
from authentik.enterprise.required_actions import USER_ATTRIBUTE_REQUIRED_ACTIONS
from authentik.enterprise.required_actions.flows import (
    RequiredActionCompleteStageView,
    resolve_required_actions,
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
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.dummy.models import DummyStage
from authentik.stages.user_login.models import UserLoginStage


def create_action_flow() -> Flow:
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


def flow_url(flow: Flow) -> str:
    return reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})


def executor_url(flow: Flow) -> str:
    return reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})


class RequiredActionsTestCase(FlowTestCase):
    def setUp(self):
        super().setUp()
        cache.delete(CACHE_KEY_ENTERPRISE_LICENSE)
        self.user = create_test_user()
        self.action = create_action_flow()
        self.require([self.action.slug])

    def require(self, value):
        self.user.attributes[USER_ATTRIBUTE_REQUIRED_ACTIONS] = value
        self.user.save()

    def open_page(self, url: str):
        return self.client.get(url, HTTP_ACCEPT="text/html")

    def assertRedirectsToAction(self, url: str, action: Flow):
        """Opening `url` sends the browser to `action`"""
        response = self.open_page(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, flow_url(action))

    def complete(self, action: Flow):
        """Complete the dummy stage of `action` and return the completion response"""
        self.assertStageResponse(
            self.client.get(executor_url(action)), action, component="ak-stage-dummy"
        )
        self.assertEqual(self.client.post(executor_url(action), {}).status_code, 302)
        return self.client.get(executor_url(action))


class TestRequiredActions(RequiredActionsTestCase):
    """Running required actions and resuming what the user was doing"""

    def login(self, *stages: DummyStage, query: str = ""):
        """Log in through an authentication flow with `stages` after the login stage"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        bindings = [
            FlowStageBinding.objects.create(
                target=flow, stage=UserLoginStage.objects.create(name=generate_id()), order=0
            )
        ]
        for order, stage in enumerate(stages, start=1):
            bindings.append(FlowStageBinding.objects.create(target=flow, stage=stage, order=order))
        plan = FlowPlan(
            flow_pk=flow.pk.hex, bindings=bindings, markers=[StageMarker()] * len(bindings)
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        self.set_flow_plan(plan)
        return flow, self.client.get(executor_url(flow), {"query": query})

    def test_resolve_preserves_order_in_one_query(self):
        second = create_action_flow()
        with self.assertNumQueries(1):
            self.assertEqual(
                resolve_required_actions([second.slug, self.action.slug, second.slug]),
                [second, self.action, second],
            )

    @enterprise_test()
    def test_login_resumes_destination(self):
        """After login, the action runs before the requested page, which is opened afterwards"""
        self.login()
        destination = reverse("authentik_providers_oauth2:authorize")
        self.assertRedirectsToAction(destination, self.action)
        self.assertStageRedirects(self.complete(self.action), destination)

        self.user.refresh_from_db()
        self.assertNotIn(USER_ATTRIBUTE_REQUIRED_ACTIONS, self.user.attributes)
        self.assertEqual(self.open_page(reverse("authentik_core:if-user")).status_code, 200)
        event = Event.objects.get(action=EventAction.REQUIRED_ACTION_COMPLETED)
        self.assertEqual(event.context["flow_slug"], self.action.slug)
        self.assertEqual(event.user, get_user(self.user))
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.MODEL_UPDATED, context__model__model_name="user"
            ).exists()
        )

    @enterprise_test()
    def test_existing_session_is_restricted(self):
        """Actions added to a logged-in user apply to their next request"""
        self.user.attributes.pop(USER_ATTRIBUTE_REQUIRED_ACTIONS)
        self.user.save()
        self.client.force_login(self.user)
        self.assertEqual(self.open_page(reverse("authentik_core:if-user")).status_code, 200)
        self.require([self.action.slug])
        self.assertRedirectsToAction(reverse("authentik_core:if-user"), self.action)

    @enterprise_test()
    def test_flow_in_progress_is_suspended(self):
        """A flow that continues after login is paused for the action and then resumed"""
        stage = DummyStage.objects.create(name=generate_id())
        query = urlencode({"next": reverse("authentik_core:if-user")})
        flow, response = self.login(stage, query=query)
        self.assertEqual(response.status_code, 302)

        response = self.client.get(executor_url(flow), {"query": query})
        self.assertStageRedirects(response, flow_url(self.action))
        self.assertStageRedirects(self.complete(self.action), f"{flow_url(flow)}?{query}")

        response = self.client.get(executor_url(flow), {"query": query})
        self.assertStageResponse(response, flow, component="ak-stage-dummy")
        response = self.client.post(f"{executor_url(flow)}?{urlencode({'query': query})}", {})
        self.assertStageRedirects(response, reverse("authentik_core:if-user"))

    @enterprise_test()
    def test_navigation_keeps_progress(self):
        """Opening another page during an action returns to it without restarting"""
        self.client.force_login(self.user)
        destination = reverse("authentik_core:if-user")
        self.assertRedirectsToAction(destination, self.action)
        self.client.get(executor_url(self.action))
        plan = self.get_flow_plan()
        self.assertRedirectsToAction(reverse("authentik_core:if-admin"), self.action)
        self.assertEqual(self.get_flow_plan().bindings, plan.bindings)
        self.assertStageRedirects(self.complete(self.action), destination)

    @enterprise_test()
    def test_direct_entry_completes(self):
        """Opening the action directly still records it as complete"""
        self.client.force_login(self.user)
        self.assertStageRedirects(
            self.complete(self.action), reverse("authentik_core:root-redirect")
        )
        self.user.refresh_from_db()
        self.assertNotIn(USER_ATTRIBUTE_REQUIRED_ACTIONS, self.user.attributes)

    @enterprise_test()
    def test_multiple_actions_run_in_order(self):
        second = create_action_flow()
        self.require([self.action.slug, second.slug])
        self.client.force_login(self.user)
        destination = reverse("authentik_core:if-user")

        self.assertRedirectsToAction(destination, self.action)
        self.assertStageRedirects(self.complete(self.action), destination)
        self.user.refresh_from_db()
        self.assertEqual(self.user.attributes[USER_ATTRIBUTE_REQUIRED_ACTIONS], [second.slug])

        self.assertRedirectsToAction(destination, second)
        self.assertStageRedirects(self.complete(second), destination)
        self.user.refresh_from_db()
        self.assertNotIn(USER_ATTRIBUTE_REQUIRED_ACTIONS, self.user.attributes)

    @enterprise_test()
    def test_single_slug(self):
        """A single flow slug works without being wrapped in a list"""
        self.require(self.action.slug)
        self.client.force_login(self.user)
        self.assertRedirectsToAction(reverse("authentik_core:if-user"), self.action)
        self.complete(self.action)
        self.user.refresh_from_db()
        self.assertNotIn(USER_ATTRIBUTE_REQUIRED_ACTIONS, self.user.attributes)

    @enterprise_test()
    def test_replaced_action_keeps_destination(self):
        """Replacing an action in progress still returns the user to their page afterwards"""
        self.client.force_login(self.user)
        destination = reverse("authentik_core:if-user")
        self.assertRedirectsToAction(destination, self.action)
        replacement = create_action_flow()
        self.require([replacement.slug])
        response = self.client.get(executor_url(self.action))
        self.assertStageRedirects(response, flow_url(replacement))
        self.assertStageRedirects(self.complete(replacement), destination)

    @enterprise_test()
    def test_completion_preserves_concurrent_updates(self):
        """An update to the user while the action runs survives its completion"""
        self.client.force_login(self.user)
        self.assertRedirectsToAction(reverse("authentik_core:if-user"), self.action)
        dispatch = RequiredActionCompleteStageView.dispatch

        def update_then_complete(view, request):
            user = User.objects.get(pk=self.user.pk)
            user.attributes["updated"] = "preserved"
            user.save(update_fields=["attributes"])
            return dispatch(view, request)

        with patch.object(RequiredActionCompleteStageView, "dispatch", update_then_complete):
            self.complete(self.action)
        self.user.refresh_from_db()
        self.assertEqual(self.user.attributes["updated"], "preserved")
        self.assertNotIn(USER_ATTRIBUTE_REQUIRED_ACTIONS, self.user.attributes)

    @enterprise_test()
    def test_invalid_actions_fail_closed(self):
        """An action that cannot run keeps the session restricted"""
        denied = create_action_flow()
        PolicyBinding.objects.create(
            policy=DummyPolicy.objects.create(
                name=generate_id(), result=False, wait_min=0, wait_max=1
            ),
            target=denied,
            order=0,
        )
        self.client.force_login(self.user)
        for value in (["does-not-exist"], [denied.slug], [42], None, False, 0, "", {}):
            with self.subTest(value=value):
                self.require(value)
                response = self.open_page(reverse("authentik_core:if-user"))
                self.assertEqual(response.status_code, 403)

    @enterprise_test(expiry=expiry_expired)
    def test_expired_license_still_enforces(self):
        self.client.force_login(self.user)
        self.assertRedirectsToAction(reverse("authentik_core:if-user"), self.action)

    def test_unlicensed_ignores_actions(self):
        self.client.force_login(self.user)
        self.assertEqual(self.open_page(reverse("authentik_core:if-user")).status_code, 200)


class TestRequiredActionsMiddleware(RequiredActionsTestCase):
    """What a session with required actions can and cannot reach"""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    @enterprise_test()
    def test_api_denied(self):
        for route in ("authentik_api:application-list", "authentik_api:flow-list"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route), HTTP_ACCEPT="application/json")
                self.assertEqual(response.status_code, 403)

    @enterprise_test()
    def test_user_cannot_remove_own_actions(self):
        """Permission to edit themselves doesn't let a user skip their actions"""
        self.user.assign_perms_to_managed_role("authentik_core.view_user")
        self.user.assign_perms_to_managed_role("authentik_core.change_user", self.user)
        response = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
            {"attributes": {}},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.attributes[USER_ATTRIBUTE_REQUIRED_ACTIONS], [self.action.slug])

    @enterprise_test()
    def test_flow_interface_reads_allowed(self):
        """The flow interface can load its configuration and user, with or without a prefix"""
        for prefix in ("", "/authentik"):
            for route in ("authentik_api:user-me", "authentik_api:config"):
                with self.subTest(prefix=prefix, route=route):
                    response = self.client.get(reverse(route), SCRIPT_NAME=prefix)
                    self.assertEqual(response.status_code, 200)

    @enterprise_test()
    def test_other_flow_redirected_to_action(self):
        other = create_test_flow(FlowDesignation.STAGE_CONFIGURATION)
        self.assertRedirectsToAction(flow_url(other), self.action)

    @enterprise_test()
    def test_logout_allowed(self):
        Flow.objects.filter(designation=FlowDesignation.INVALIDATION).delete()
        invalidation = create_test_flow(FlowDesignation.INVALIDATION)
        response = self.client.get(reverse("authentik_flows:default-invalidation"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, flow_url(invalidation))
        self.assertEqual(self.open_page(flow_url(invalidation)).status_code, 200)

    @enterprise_test()
    def test_impersonation_not_restricted(self):
        """An administrator impersonating the user isn't sent through their actions"""
        self.client.force_login(create_test_admin_user())
        self.client.post(
            reverse("authentik_api:user-impersonate", kwargs={"pk": self.user.pk}),
            data={"reason": generate_id()},
        )
        self.assertEqual(self.open_page(reverse("authentik_core:if-user")).status_code, 200)
        self.assertNotIn(SESSION_KEY_PLAN, self.client.session)
