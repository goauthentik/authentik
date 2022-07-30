"""captcha tests"""
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.captcha.models import CaptchaStage

# https://developers.google.com/recaptcha/docs/faq#id-like-to-run-automated-tests-with-recaptcha.-what-should-i-do
RECAPTCHA_PUBLIC_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"


class TestCaptchaStage(FlowTestCase):
    """Captcha tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)

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
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
