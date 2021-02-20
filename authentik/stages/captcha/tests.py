"""captcha tests"""
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import User
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.stages.captcha.models import CaptchaStage


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
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_valid(self):
        """Test valid captcha"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            {"g-recaptcha-response": "PASSED"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"type": "redirect", "to": reverse("authentik_core:shell")},
        )
