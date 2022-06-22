"""consent tests"""
from time import sleep

from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tasks import clean_expired_models
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.consent.models import ConsentMode, ConsentStage, UserConsent


class TestConsentStage(FlowTestCase):
    """Consent tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.application = Application.objects.create(
            name="test-application",
            slug="test-application",
        )

    def test_always_required(self):
        """Test always required consent"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name="consent", mode=ConsentMode.ALWAYS_REQUIRE)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(flow_pk=flow.pk.hex, bindings=[binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        # pylint: disable=no-member
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertFalse(UserConsent.objects.filter(user=self.user).exists())

    def test_permanent(self):
        """Test permanent consent from user"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name="consent", mode=ConsentMode.PERMANENT)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
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
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(user=self.user, application=self.application).exists()
        )

    def test_expire(self):
        """Test expiring consent from user"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(
            name="consent", mode=ConsentMode.EXPIRING, consent_expire_in="seconds=1"
        )
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
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
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(user=self.user, application=self.application).exists()
        )
        sleep(1)
        clean_expired_models.delay().get()
        self.assertFalse(
            UserConsent.objects.filter(user=self.user, application=self.application).exists()
        )
