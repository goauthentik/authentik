"""login tests"""
from time import sleep
from unittest.mock import patch

from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core.cache import cache
from django.urls import reverse
from django.utils.timezone import now

from authentik.core.models import AuthenticatedSession
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.lib.utils.http import DEFAULT_IP
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.user_login.models import UserLoginStage


class TestUserLoginStage(FlowTestCase):
    """Login tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()

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
        other_session = AuthenticatedSession.objects.create(
            user=self.user,
            session_key=key,
            last_ip=DEFAULT_IP,
        )
        cache.set(f"{KEY_PREFIX}{other_session.session_key}", "foo")

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertFalse(AuthenticatedSession.objects.filter(session_key=key))
        self.assertFalse(cache.has_key(f"{KEY_PREFIX}{key}"))

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
        session = AuthenticatedSession.objects.filter(session_key=session_key).first()
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

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"remember_me": True},
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertNotEqual(list(self.client.session.keys()), [])
        session_key = self.client.session.session_key
        session = AuthenticatedSession.objects.filter(session_key=session_key).first()
        self.assertAlmostEqual(
            session.expires.timestamp() - now().timestamp(),
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
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        response = self.client.get(reverse("authentik_api:application-list"))
        self.assertEqual(response.status_code, 403)
