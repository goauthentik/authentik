"""flow views tests"""

from urllib.parse import urlencode

from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_PLAN


class TestHelperView(FlowTestCase):
    """Test helper views logic"""

    def test_default_view(self):
        """Test that ToDefaultFlow returns the expected URL"""
        Flow.objects.filter(designation=FlowDesignation.INVALIDATION).delete()
        flow = create_test_flow(FlowDesignation.INVALIDATION)
        response = self.client.get(
            reverse("authentik_flows:default-invalidation"),
        )
        expected_url = reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

    def test_default_view_invalid_plan(self):
        """Test that ToDefaultFlow returns the expected URL (with an invalid plan)"""
        Flow.objects.filter(designation=FlowDesignation.INVALIDATION).delete()
        flow = create_test_flow(FlowDesignation.INVALIDATION)
        plan = FlowPlan(flow_pk=flow.pk.hex + "aa")
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_flows:default-invalidation"),
        )
        expected_url = reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

    def test_cancel_strips_login_hint(self):
        """login_hint must be stripped from `next` on cancel so it can't re-prefill (#25476)"""
        cancel_url = reverse("authentik_flows:cancel")
        next_url = "/application/o/authorize/?" + urlencode(
            {"client_id": "test", "login_hint": "foo@authentik.company", "state": "abc"}
        )
        response = self.client.get(cancel_url, {NEXT_ARG_NAME: next_url})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("login_hint", response.url)
        # Other params are preserved
        self.assertIn("client_id=test", response.url)
        self.assertIn("state=abc", response.url)

    def test_cancel_preserves_next_without_login_hint(self):
        """A `next` without login_hint is redirected to unchanged"""
        cancel_url = reverse("authentik_flows:cancel")
        next_url = "/application/o/authorize/?" + urlencode({"client_id": "test"})
        response = self.client.get(cancel_url, {NEXT_ARG_NAME: next_url})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)
