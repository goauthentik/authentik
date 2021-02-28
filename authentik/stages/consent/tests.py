"""consent tests"""
from time import sleep

from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import Application, User
from authentik.core.tasks import clean_expired_models
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlan
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.stages.consent.models import ConsentMode, ConsentStage, UserConsent


class TestConsentStage(TestCase):
    """Consent tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="unittest", email="test@beryju.org"
        )
        self.application = Application.objects.create(
            name="test-application",
            slug="test-application",
        )
        self.client = Client()

    def test_always_required(self):
        """Test always required consent"""
        flow = Flow.objects.create(
            name="test-consent",
            slug="test-consent",
            designation=FlowDesignation.AUTHENTICATION,
        )
        stage = ConsentStage.objects.create(
            name="consent", mode=ConsentMode.ALWAYS_REQUIRE
        )
        FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(flow_pk=flow.pk.hex, stages=[stage], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"to": reverse("authentik_core:shell"), "type": "redirect"},
        )
        self.assertFalse(UserConsent.objects.filter(user=self.user).exists())

    def test_permanent(self):
        """Test permanent consent from user"""
        self.client.force_login(self.user)
        flow = Flow.objects.create(
            name="test-consent",
            slug="test-consent",
            designation=FlowDesignation.AUTHENTICATION,
        )
        stage = ConsentStage.objects.create(name="consent", mode=ConsentMode.PERMANENT)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            stages=[stage],
            markers=[StageMarker()],
            context={PLAN_CONTEXT_APPLICATION: self.application},
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"to": reverse("authentik_core:shell"), "type": "redirect"},
        )
        self.assertTrue(
            UserConsent.objects.filter(
                user=self.user, application=self.application
            ).exists()
        )

    def test_expire(self):
        """Test expiring consent from user"""
        self.client.force_login(self.user)
        flow = Flow.objects.create(
            name="test-consent",
            slug="test-consent",
            designation=FlowDesignation.AUTHENTICATION,
        )
        stage = ConsentStage.objects.create(
            name="consent", mode=ConsentMode.EXPIRING, consent_expire_in="seconds=1"
        )
        FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            stages=[stage],
            markers=[StageMarker()],
            context={PLAN_CONTEXT_APPLICATION: self.application},
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"to": reverse("authentik_core:shell"), "type": "redirect"},
        )
        self.assertTrue(
            UserConsent.objects.filter(
                user=self.user, application=self.application
            ).exists()
        )
        sleep(1)
        clean_expired_models.delay().get()
        self.assertFalse(
            UserConsent.objects.filter(
                user=self.user, application=self.application
            ).exists()
        )
