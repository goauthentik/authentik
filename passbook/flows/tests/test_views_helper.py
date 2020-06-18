"""flow views tests"""
from django.shortcuts import reverse
from django.test import Client, TestCase

from passbook.flows.models import Flow, FlowDesignation
from passbook.flows.planner import FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN


class TestHelperView(TestCase):
    """Test helper views logic"""

    def setUp(self):
        self.client = Client()

    def test_default_view(self):
        """Test that ToDefaultFlow returns the expected URL"""
        flow = Flow.objects.filter(designation=FlowDesignation.INVALIDATION,).first()
        response = self.client.get(reverse("passbook_flows:default-invalidation"),)
        expected_url = reverse(
            "passbook_flows:flow-executor-shell", kwargs={"flow_slug": flow.slug}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

    def test_default_view_invalid_plan(self):
        """Test that ToDefaultFlow returns the expected URL (with an invalid plan)"""
        flow = Flow.objects.filter(designation=FlowDesignation.INVALIDATION,).first()
        plan = FlowPlan(flow_pk=flow.pk.hex + "aa")
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(reverse("passbook_flows:default-invalidation"),)
        expected_url = reverse(
            "passbook_flows:flow-executor-shell", kwargs={"flow_slug": flow.slug}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
