"""captcha tests"""
from django.conf import settings
from django.shortcuts import reverse
from django.test import Client, TestCase

from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.captcha.models import CaptchaStage


class TestCaptchaStage(TestCase):
    """Captcha tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="unittest", email="test@beryju.org"
        )
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-captcha",
            slug="test-captcha",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = CaptchaStage.objects.create(
            name="captcha",
            public_key=settings.RECAPTCHA_PUBLIC_KEY,
            private_key=settings.RECAPTCHA_PRIVATE_KEY,
        )
        FlowStageBinding.objects.create(flow=self.flow, stage=self.stage, order=2)

    def test_valid(self):
        """Test valid captcha"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            {"g-recaptcha-response": "PASSED"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_core:overview"))
