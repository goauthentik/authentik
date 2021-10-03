"""consent tests"""
from time import sleep

from django.urls import reverse
from django.utils.encoding import force_str
from rest_framework.test import APITestCase

from authentik.core.models import Application, User
from authentik.core.tasks import clean_expired_models
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.consent.models import ConsentMode, ConsentStage, UserConsent


class TestConsentStage(APITestCase):
    """Consent tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="unittest", email="test@beryju.org")
        self.application = Application.objects.create(
            name="test-application",
            slug="test-application",
        )

    def test_always_required(self):
        """Test always required consent"""
        flow = Flow.objects.create(
            name="test-consent",
            slug="test-consent",
            designation=FlowDesignation.AUTHENTICATION,
        )
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
        self.assertJSONEqual(
            # pylint: disable=no-member
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
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
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )
        self.assertTrue(
            UserConsent.objects.filter(user=self.user, application=self.application).exists()
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
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )
        self.assertTrue(
            UserConsent.objects.filter(user=self.user, application=self.application).exists()
        )
        sleep(1)
        clean_expired_models.delay().get()
        self.assertFalse(
            UserConsent.objects.filter(user=self.user, application=self.application).exists()
        )
