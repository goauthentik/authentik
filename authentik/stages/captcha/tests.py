"""captcha tests"""
from django.urls import reverse
from django.utils.encoding import force_str
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.captcha.models import CaptchaStage

# https://developers.google.com/recaptcha/docs/faq#id-like-to-run-automated-tests-with-recaptcha.-what-should-i-do
RECAPTCHA_PUBLIC_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"


class TestCaptchaStage(APITestCase):
    """Captcha tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="unittest", email="test@beryju.org")

        self.flow = Flow.objects.create(
            name="test-captcha",
            slug="test-captcha",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = CaptchaStage.objects.create(
            name="captcha",
            public_key=RECAPTCHA_PUBLIC_KEY,
            private_key=RECAPTCHA_PRIVATE_KEY,
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_valid(self):
        """Test valid captcha"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"token": "PASSED"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )
