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
from authentik.flows.tests import APIFlowTestCase
from authentik.lib.generators import generate_id
from authentik.stages.consent.models import ConsentMode, ConsentStage, UserConsent
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
    PLAN_CONTEXT_CONSENT_TOKEN,
)


class TestConsentStage(APIFlowTestCase):
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
        self.set_flow_plan(plan)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

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
        self.set_flow_plan(plan)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": self.get_flow_plan().context[PLAN_CONTEXT_CONSENT_TOKEN],
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
        self.set_flow_plan(plan)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {
                "token": self.get_flow_plan().context[PLAN_CONTEXT_CONSENT_TOKEN],
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
        self.set_flow_plan(plan)
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

    def test_expire_reconsent(self):
        """Test consenting again after consent expired but before it was cleaned up"""
        self.client.force_login(self.user)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage = ConsentStage.objects.create(
            name=generate_id(), mode=ConsentMode.EXPIRING, consent_expire_in="seconds=1"
        )
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=2)
        permissions = [PermissionDict(id="foo", name="foo-desc")]

        def consent():
            plan = FlowPlan(
                flow_pk=flow.pk.hex,
                bindings=[binding],
                markers=[StageMarker()],
                context={
                    PLAN_CONTEXT_APPLICATION: self.application,
                    PLAN_CONTEXT_CONSENT_PERMISSIONS: permissions,
                },
            )
            self.set_flow_plan(plan)
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            )
            raw_res = self.assertStageResponse(
                response,
                flow,
                self.user,
                permissions=[{"id": "foo", "name": "foo-desc"}],
                additional_permissions=[],
            )
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                {"token": raw_res["token"]},
            )
            self.assertEqual(response.status_code, 200)
            self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

        consent()
        with freeze_time() as frozen_time:
            frozen_time.tick(timedelta(seconds=3))
            # The expired consent is hidden from the default manager, but still exists
            # as `clean_expired_models` hasn't run yet
            self.assertFalse(
                UserConsent.objects.filter(user=self.user, application=self.application).exists()
            )
            consent()
            self.assertEqual(
                UserConsent.objects.including_expired()
                .filter(user=self.user, application=self.application)
                .count(),
                1,
            )
            self.assertTrue(
                UserConsent.objects.filter(
                    user=self.user, application=self.application, permissions="foo"
                ).exists()
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
        self.set_flow_plan(plan)

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
        self.set_flow_plan(plan)

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
        self.set_flow_plan(plan)

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
        self.set_flow_plan(plan)

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {},
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(response, component="xak-flow-redirect")
