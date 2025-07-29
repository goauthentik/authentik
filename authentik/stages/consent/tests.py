"""consent tests"""

from datetime import timedelta

from django.urls import reverse
from freezegun import freeze_time

from authentik.core.models import Application
from authentik.core.tasks import clean_expired_models
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.challenge import PermissionDict
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.stages.consent.models import ConsentMode, ConsentStage, UserConsent
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
    SESSION_KEY_CONSENT_TOKEN,
)


class TestConsentStage(FlowTestCase):
    """Consent tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )

    def test_mismatched_token(self):
        """Test incorrect token"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.ALWAYS_REQUIRE)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(flow_pk=flow.pk.hex, bindings=[binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

        session = self.client.session
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": generate_id(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(
            response,
            flow,
            component="ak-stage-consent",
            response_errors={
                "token": [{"string": "Invalid consent token, re-showing prompt", "code": "invalid"}]
            },
        )
        self.assertFalse(UserConsent.objects.filter(user=self.user).exists())

    def test_always_required(self):
        """Test always required consent"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.ALWAYS_REQUIRE)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(flow_pk=flow.pk.hex, bindings=[binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

        session = self.client.session
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": session[SESSION_KEY_CONSENT_TOKEN],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertFalse(UserConsent.objects.filter(user=self.user).exists())

    def test_permanent(self):
        """Test permanent consent from user"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.PERMANENT)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

        session = self.client.session
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": session[SESSION_KEY_CONSENT_TOKEN],
            },
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
            name=generate_id(), mode=ConsentMode.EXPIRING, consent_expire_in="seconds=1"
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
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        raw_res = self.assertStageResponse(
            response,
            flow,
            self.user,
            permissions=[],
            additional_permissions=[],
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": raw_res["token"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(user=self.user, application=self.application).exists()
        )
        with freeze_time() as frozen_time:
            frozen_time.tick(timedelta(seconds=3))
            clean_expired_models.send()
            self.assertFalse(
                UserConsent.objects.filter(user=self.user, application=self.application).exists()
            )

    def test_permanent_more_perms(self):
        """Test permanent consent from user"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.PERMANENT)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
                PLAN_CONTEXT_CONSENT_PERMISSIONS: [PermissionDict(id="foo", name="foo-desc")],
                PLAN_CONTEXT_CONSENT_HEADER: "test header",
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        # First, consent with a single permission
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        raw_res = self.assertStageResponse(
            response,
            flow,
            self.user,
            permissions=[
                {"id": "foo", "name": "foo-desc"},
            ],
            additional_permissions=[],
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": raw_res["token"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(
                user=self.user, application=self.application, permissions="foo"
            ).exists()
        )

        # Request again with more perms
        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
                PLAN_CONTEXT_CONSENT_PERMISSIONS: [
                    PermissionDict(id="foo", name="foo-desc"),
                    PermissionDict(id="bar", name="bar-desc"),
                ],
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        raw_res = self.assertStageResponse(
            response,
            flow,
            self.user,
            permissions=[
                {"id": "foo", "name": "foo-desc"},
            ],
            additional_permissions=[
                {"id": "bar", "name": "bar-desc"},
            ],
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": raw_res["token"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(
                user=self.user, application=self.application, permissions="foo bar"
            ).exists()
        )

    def test_permanent_same(self):
        """Test permanent consent from user"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.PERMANENT)
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        # First, consent with a single permission
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        raw_res = self.assertStageResponse(
            response,
            flow,
            self.user,
            permissions=[],
            additional_permissions=[],
        )
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": raw_res["token"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertTrue(
            UserConsent.objects.filter(
                user=self.user, application=self.application, permissions=""
            ).exists()
        )

        # Request again with the same perms
        plan = FlowPlan(
            flow_pk=flow.pk.hex,
            bindings=[binding],
            markers=[StageMarker()],
            context={
                PLAN_CONTEXT_APPLICATION: self.application,
                PLAN_CONTEXT_CONSENT_PERMISSIONS: [],
            },
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(response, component="xak-flow-redirect")
