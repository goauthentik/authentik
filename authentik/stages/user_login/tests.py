"""login tests"""

from time import sleep
from unittest.mock import patch

from django.conf import settings
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.http import HttpRequest
from django.urls import reverse
from django.utils.timezone import now

from authentik.blueprints.tests import apply_blueprint
from authentik.core import user_switching
from authentik.core.models import (
    USER_ATTRIBUTE_NEXT_ACTIONS,
    AuthenticatedSession,
    Session,
    User,
    UserSwitchingSession,
)
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.enterprise.license import CACHE_KEY_ENTERPRISE_LICENSE
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
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, PLAN_CONTEXT_REDIRECT, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.dummy.models import DummyStage
from authentik.stages.user_login.middleware import (
    SESSION_KEY_BINDING_NET,
    BoundSessionMiddleware,
    SessionBindingBroken,
    logout_extra,
)
from authentik.stages.user_login.models import GeoIPBinding, NetworkBinding, UserLoginStage
from authentik.stages.user_login.next_actions import SESSION_KEY_PENDING_NEXT_ACTIONS


class TestUserLoginStage(FlowTestCase):
    """Login tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_user()

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = UserLoginStage.objects.create(name="login")
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_valid_get(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_stale_user_switching_cookie_is_replaced(self):
        """A signed cookie without a switching session does not break login."""
        stale_token = generate_id(user_switching.TOKEN_LENGTH)
        self.client.cookies[settings.USER_SWITCHING_COOKIE_NAME] = user_switching.encode_cookie(
            stale_token
        )
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex,
            bindings=[self.binding],
            markers=[StageMarker()],
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        switching_session = UserSwitchingSession.objects.get(authenticated_sessions__user=self.user)
        self.assertNotEqual(switching_session.token, stale_token)
        self.assertEqual(
            user_switching.decode_cookie(
                self.client.cookies[settings.USER_SWITCHING_COOKIE_NAME].value
            ),
            switching_session.token,
        )

    def test_valid_post(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_session_fixation_key_rotated_on_login(self):
        """Security regression (CWE-384): the session key must rotate on login
        so a pre-login session identifier known to an attacker can't be reused.
        Django's ``login()`` provides this via ``cycle_key()``; pinned here
        end-to-end through the flow executor and custom session backend."""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        pre_login_key = session.session_key
        self.assertIsNotNone(pre_login_key)
        # Unauthenticated session persisted before login...
        self.assertTrue(Session.objects.filter(session_key=pre_login_key).exists())

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

        post_login_key = self.client.session.session_key
        # ...the identifier must change on authentication...
        self.assertIsNotNone(post_login_key)
        self.assertNotEqual(pre_login_key, post_login_key)
        # ...the pre-login key must no longer exist...
        self.assertFalse(Session.objects.filter(session_key=pre_login_key).exists())
        self.assertFalse(
            AuthenticatedSession.objects.filter(session__session_key=pre_login_key).exists()
        )
        # ...and only the rotated key may be bound to the authenticated user.
        self.assertTrue(
            AuthenticatedSession.objects.filter(
                session__session_key=post_login_key, user=self.user
            ).exists()
        )

    def test_terminate_other_sessions(self):
        """Test terminate_other_sessions"""
        self.stage.terminate_other_sessions = True
        self.stage.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        key = generate_id()
        AuthenticatedSession.objects.create(
            session=Session.objects.create(
                session_key=key,
                last_ip=ClientIPMiddleware.default_ip,
            ),
            user=self.user,
        )

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertFalse(AuthenticatedSession.objects.filter(session__session_key=key))
        self.assertFalse(Session.objects.filter(session_key=key).exists())

    def test_second_login_replaces_existing_session(self):
        """Test ordinary cross-user login keeps Django's session replacement behavior."""
        other_user = create_test_user()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        first_session_key = self.client.session.session_key

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = other_user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        second_session_key = self.client.session.session_key
        self.assertNotEqual(first_session_key, second_session_key)
        second = AuthenticatedSession.objects.get(session__session_key=second_session_key)
        self.assertEqual(second.user, other_user)
        self.assertTrue(second.is_current)
        self.assertFalse(
            AuthenticatedSession.objects.filter(session__session_key=first_session_key).exists()
        )
        self.assertFalse(Session.objects.filter(session_key=first_session_key).exists())

    def test_relogin_same_user_keeps_single_session(self):
        """Test re-logging in as the same user doesn't accumulate sessions"""
        for _ in range(2):
            plan = FlowPlan(
                flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()]
            )
            plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
            session = self.client.session
            session[SESSION_KEY_PLAN] = plan
            session.save()
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            )
            self.assertEqual(response.status_code, 200)

        self.assertEqual(AuthenticatedSession.objects.filter(user=self.user).count(), 1)
        self.assertIsNotNone(
            AuthenticatedSession.objects.get(user=self.user).user_switching_session_id
        )

    def test_expiry(self):
        """Test with expiry"""
        self.stage.session_duration = "seconds=2"
        self.stage.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        before_request = now()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertNotEqual(list(self.client.session.keys()), [])
        session_key = self.client.session.session_key
        session = Session.objects.filter(session_key=session_key).first()
        self.assertAlmostEqual(
            session.expires.timestamp() - before_request.timestamp(),
            timedelta_from_string(self.stage.session_duration).total_seconds(),
            delta=1,
        )
        sleep(3)
        self.client.session.clear_expired()
        self.assertEqual(list(self.client.session.keys()), [])

    def test_expiry_remember(self):
        """Test with expiry"""
        self.stage.session_duration = "seconds=2"
        self.stage.remember_me_offset = "seconds=2"
        self.stage.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(response, component="ak-stage-user-login")

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"remember_me": True},
        )
        _now = now().timestamp()
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertNotEqual(list(self.client.session.keys()), [])
        session_key = self.client.session.session_key
        session = Session.objects.filter(session_key=session_key).first()
        self.assertAlmostEqual(
            session.expires.timestamp() - _now,
            timedelta_from_string(self.stage.session_duration).total_seconds()
            + timedelta_from_string(self.stage.remember_me_offset).total_seconds(),
            delta=1,
        )
        sleep(5)
        self.client.session.clear_expired()
        self.assertEqual(list(self.client.session.keys()), [])

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_without_user(self):
        """Test a plan without any pending user, resulting in a denied"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
        )

    @apply_blueprint("default/flow-default-user-settings-flow.yaml")
    def test_inactive_account(self):
        """Test with a valid pending user and backend"""
        self.user.is_active = False
        self.user.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(
            response, self.flow, component="ak-stage-access-denied", error_message="Unknown error"
        )

        # Check that API requests get rejected
        response = self.client.get(reverse("authentik_api:application-list"))
        self.assertEqual(response.status_code, 403)

        # Check that flow requests requiring a user also get rejected
        response = self.client.get(
            reverse(
                "authentik_api:flow-executor",
                kwargs={"flow_slug": "default-user-settings-flow"},
            )
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="Flow does not apply to current user.",
        )

    def test_unsaved_pending_user(self):
        """Test that a pending user with no pk (unsaved) causes stage_invalid."""
        unsaved = User()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = unsaved
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(response, self.flow, component="ak-stage-access-denied")

    def test_binding_net_break_log(self):
        """Test logout_extra with exception"""
        # IPs from https://github.com/maxmind/MaxMind-DB/blob/main/source-data/GeoLite2-ASN-Test.json
        for args, expect in [
            [[NetworkBinding.BIND_ASN, "8.8.8.8", "8.8.8.8"], ["network.missing"]],
            [[NetworkBinding.BIND_ASN, "1.0.0.1", "1.128.0.1"], ["network.asn"]],
            [
                [NetworkBinding.BIND_ASN_NETWORK, "12.81.96.1", "12.81.128.1"],
                ["network.asn_network"],
            ],
            [[NetworkBinding.BIND_ASN_NETWORK_IP, "1.0.0.1", "1.0.0.2"], ["network.ip"]],
        ]:
            with self.subTest(args[0]):
                with self.assertRaises(SessionBindingBroken) as cm:
                    BoundSessionMiddleware.recheck_session_net(*args)
                self.assertEqual(cm.exception.reason, expect[0])
                # Ensure the request can be logged without throwing errors
                self.client.force_login(self.user)
                request = HttpRequest()
                request.session = self.client.session
                request.user = self.user
                logout_extra(request, cm.exception)

    def test_binding_geo_break_log(self):
        """Test logout_extra with exception"""
        # IPs from https://github.com/maxmind/MaxMind-DB/blob/main/source-data/GeoLite2-City-Test.json
        for args, expect in [
            [[GeoIPBinding.BIND_CONTINENT, "8.8.8.8", "8.8.8.8"], ["geoip.missing"]],
            [[GeoIPBinding.BIND_CONTINENT, "2.125.160.216", "67.43.156.1"], ["geoip.continent"]],
            [
                [GeoIPBinding.BIND_CONTINENT_COUNTRY, "81.2.69.142", "89.160.20.112"],
                ["geoip.country"],
            ],
            [
                [GeoIPBinding.BIND_CONTINENT_COUNTRY_CITY, "2.125.160.216", "81.2.69.142"],
                ["geoip.city"],
            ],
        ]:
            with self.subTest(args[0]):
                with self.assertRaises(SessionBindingBroken) as cm:
                    BoundSessionMiddleware.recheck_session_geo(*args)
                self.assertEqual(cm.exception.reason, expect[0])
                # Ensure the request can be logged without throwing errors
                self.client.force_login(self.user)
                request = HttpRequest()
                request.session = self.client.session
                request.user = self.user
                logout_extra(request, cm.exception)

    def test_session_binding_broken(self):
        """Test session binding"""
        Event.objects.all().delete()
        self.client.force_login(self.user)
        session = self.client.session
        session[Session.Keys.LAST_IP] = "192.0.2.1"
        session[SESSION_KEY_BINDING_NET] = NetworkBinding.BIND_ASN_NETWORK_IP
        session.save()

        res = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res.url,
            reverse(
                "authentik_flows:default-authentication",
            )
            + f"?{NEXT_ARG_NAME}={reverse('authentik_api:user-me')}",
        )
        event = Event.objects.filter(action=EventAction.LOGOUT).first()
        self.assertEqual(event.user, get_user(self.user))


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

    def test_html_request_redirects_to_actions(self):
        """A browser request is sent into the pending action flows"""
        response = self.client.get(reverse("authentik_core:if-user"), HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.action.slug}),
        )
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_REDIRECT], reverse("authentik_core:if-user"))

    def test_api_request_denied(self):
        """A non-HTML request is denied instead of redirected"""
        response = self.client.get(
            reverse("authentik_api:application-list"), HTTP_ACCEPT="application/json"
        )
        self.assertEqual(response.status_code, 403)

    def test_allowed_paths_pass(self):
        """The flow executor and user info APIs needed to complete actions stay reachable"""
        response = self.client.get(reverse("authentik_api:user-me"), HTTP_ACCEPT="application/json")
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

    def test_unresolvable_actions_stay_blocked(self):
        """A broken attribute does not fail open."""
        self.user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS] = ["does-not-exist"]
        self.user.save()
        response = self.client.get(reverse("authentik_core:if-user"), HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.session[SESSION_KEY_PENDING_NEXT_ACTIONS])
