"""Stage marker tests"""

from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from authentik.core.tests.utils import RequestFactory, create_test_flow, create_test_user
from authentik.events.models import Event, EventAction
from authentik.flows.markers import ReevaluateMarker
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.lib.generators import generate_id
from authentik.policies.types import PolicyResult
from authentik.stages.dummy.models import DummyStage
from authentik.stages.user_login.models import UserLoginStage


class TestReevaluateMarkerLoginBlocked(TestCase):
    """A user-login stage dropped by a failed policy re-evaluation emits a
    login_blocked event; nothing else does."""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.flow = create_test_flow()
        self.user = create_test_user()

    def _request(self, user=None):
        request = self.request_factory.get("/")
        request.user = user or AnonymousUser()
        return request

    def _binding(self, stage):
        return FlowStageBinding.objects.create(
            target=self.flow, stage=stage, order=0, re_evaluate_policies=True
        )

    def _plan(self, **context):
        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context.update(context)
        return plan

    def _process(self, binding, result, plan, request):
        marker = ReevaluateMarker(binding=binding)
        with patch("authentik.flows.markers.PolicyEngine") as engine:
            engine.return_value.result = result
            return marker.process(plan, binding, request)

    def _blocked_events(self):
        return Event.objects.filter(action=EventAction.LOGIN_BLOCKED)

    def test_login_blocked_emitted(self):
        """A failed re-evaluation of a user-login stage emits one login_blocked event
        carrying the pending user as subject, the denial reasons, and the message."""
        binding = self._binding(UserLoginStage.objects.create(name=generate_id()))
        result = PolicyResult(False, "too far", reasons={"impossible_travel"})
        plan = self._plan(**{PLAN_CONTEXT_PENDING_USER: self.user})

        returned = self._process(binding, result, plan, self._request(self.user))

        self.assertIsNone(returned)
        event = self._blocked_events().get()
        self.assertEqual(event.context["subject"]["pk"], self.user.pk)
        self.assertEqual(event.context["reasons"], ["impossible_travel"])
        self.assertEqual(event.context["message"], "too far")
        self.assertEqual(event.user["pk"], self.user.pk)

    def test_message_falls_back_when_policy_is_silent(self):
        """A denial with no messages still emits, with a generic fallback message."""
        binding = self._binding(UserLoginStage.objects.create(name=generate_id()))
        result = PolicyResult(False, reasons={"forbidden_country"})
        plan = self._plan(**{PLAN_CONTEXT_PENDING_USER: self.user})

        self._process(binding, result, plan, self._request(self.user))

        event = self._blocked_events().get()
        self.assertEqual(event.context["message"], "Login blocked by policy.")
        self.assertEqual(event.context["reasons"], ["forbidden_country"])

    def test_not_emitted_when_passing(self):
        """A passing re-evaluation keeps the stage and emits nothing."""
        binding = self._binding(UserLoginStage.objects.create(name=generate_id()))
        plan = self._plan(**{PLAN_CONTEXT_PENDING_USER: self.user})

        returned = self._process(binding, PolicyResult(True), plan, self._request(self.user))

        self.assertEqual(returned, binding)
        self.assertFalse(self._blocked_events().exists())

    def test_not_emitted_for_non_login_stage(self):
        """A failed re-evaluation of a non-login stage drops it but emits nothing."""
        binding = self._binding(DummyStage.objects.create(name=generate_id()))
        result = PolicyResult(False, "nope", reasons={"forbidden_country"})
        plan = self._plan(**{PLAN_CONTEXT_PENDING_USER: self.user})

        returned = self._process(binding, result, plan, self._request(self.user))

        self.assertIsNone(returned)
        self.assertFalse(self._blocked_events().exists())

    def test_login_blocked_anonymous_no_subject(self):
        """A block before identification (anonymous pending user) must not crash on
        `user.uuid` and emits an event with no subject."""
        binding = self._binding(UserLoginStage.objects.create(name=generate_id()))
        result = PolicyResult(False, "nope", reasons={"forbidden_country"})
        plan = self._plan()  # no pending user -> falls back to the anonymous request user

        returned = self._process(binding, result, plan, self._request())

        self.assertIsNone(returned)
        event = self._blocked_events().get()
        self.assertIsNone(event.context["subject"])
