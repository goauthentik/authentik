"""login tests"""

from time import sleep
from unittest.mock import patch

from django.http import HttpRequest
from django.urls import reverse
from django.utils.timezone import now

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.events.models import Event, EventAction
from authentik.events.utils import get_user
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.lib.utils.time import timedelta_from_string
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.user_login.middleware import (
    SESSION_KEY_BINDING_NET,
    BoundSessionMiddleware,
    SessionBindingBroken,
    logout_extra,
)
from authentik.stages.user_login.models import GeoIPBinding, NetworkBinding, UserLoginStage


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
            + f"?{NEXT_ARG_NAME}={reverse("authentik_api:user-me")}",
        )
        event = Event.objects.filter(action=EventAction.LOGOUT).first()
        self.assertEqual(event.user, get_user(self.user))
