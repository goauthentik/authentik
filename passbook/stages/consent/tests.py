"""consent tests"""
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils.encoding import force_text

from passbook.core.models import User
from passbook.flows.markers import StageMarker
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.consent.models import ConsentStage


class TestConsentStage(TestCase):
    """Consent tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="unittest", email="test@beryju.org"
        )
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-consent",
            slug="test-consent",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = ConsentStage.objects.create(name="consent",)
        FlowStageBinding.objects.create(flow=self.flow, stage=self.stage, order=2)

    def test_valid(self):
        """Test valid consent"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            {},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            {"type": "redirect", "to": reverse("passbook_core:overview")},
        )
