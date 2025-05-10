"""Test Redirect stage"""

from urllib.parse import urlencode

from django.urls.base import reverse
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_flow
from authentik.crypto.generators import generate_id
from authentik.flows.models import FlowAuthenticationRequirement, FlowDesignation, FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.dummy.models import DummyStage
from authentik.stages.redirect.api import RedirectStageSerializer
from authentik.stages.redirect.models import RedirectMode, RedirectStage

URL = "https://url.test/"
URL_OVERRIDE = "https://urloverride.test/"


class TestRedirectStage(FlowTestCase):
    """Test Redirect stage API"""

    def setUp(self):
        super().setUp()
        self.target_flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.dummy_stage = DummyStage.objects.create(name="dummy")
        FlowStageBinding.objects.create(target=self.target_flow, stage=self.dummy_stage, order=0)
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = RedirectStage.objects.create(
            name="redirect",
            keep_context=True,
            mode=RedirectMode.STATIC,
            target_static=URL,
            target_flow=self.target_flow,
        )
        self.binding = FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )

    def test_static(self):
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageRedirects(response, URL)

    def test_flow(self):
        self.stage.mode = RedirectMode.FLOW
        self.stage.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageRedirects(
            response, reverse("authentik_core:if-flow", kwargs={"flow_slug": self.target_flow.slug})
        )

    def test_flow_query(self):
        self.stage.mode = RedirectMode.FLOW
        self.stage.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            + "?"
            + urlencode({"query": urlencode({"test": "foo"})})
        )

        self.assertStageRedirects(
            response,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.target_flow.slug})
            + "?"
            + urlencode({"test": "foo"}),
        )

    def test_override_static(self):
        policy = ExpressionPolicy.objects.create(
            name=generate_id(),
            expression=f"context['flow_plan'].context['redirect_stage_target'] = "
            f"'{URL_OVERRIDE}'; return True",
        )
        PolicyBinding.objects.create(policy=policy, target=self.binding, order=0)

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageRedirects(response, URL_OVERRIDE)

    def test_override_flow(self):
        target_flow_override = create_test_flow(FlowDesignation.AUTHENTICATION)
        dummy_stage_override = DummyStage.objects.create(name="dummy_override")
        FlowStageBinding.objects.create(
            target=target_flow_override, stage=dummy_stage_override, order=0
        )
        policy = ExpressionPolicy.objects.create(
            name=generate_id(),
            expression=f"context['flow_plan'].context['redirect_stage_target'] = "
            f"'ak-flow://{target_flow_override.slug}'; return True",
        )
        PolicyBinding.objects.create(policy=policy, target=self.binding, order=0)

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageRedirects(
            response,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": target_flow_override.slug}),
        )

    def test_override_nonexistant_flow(self):
        policy = ExpressionPolicy.objects.create(
            name=generate_id(),
            expression="context['flow_plan'].context['redirect_stage_target'] = "
            "'ak-flow://nonexistent'; return True",
        )
        PolicyBinding.objects.create(policy=policy, target=self.binding, order=0)

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageRedirects(response, URL)

    def test_target_flow_requires_redirect(self):
        self.target_flow.authentication = FlowAuthenticationRequirement.REQUIRE_REDIRECT
        self.target_flow.save()
        self.stage.mode = RedirectMode.FLOW
        self.stage.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageRedirects(
            response, reverse("authentik_core:if-flow", kwargs={"flow_slug": self.target_flow.slug})
        )

    def test_target_flow_non_applicable(self):
        self.target_flow.authentication = FlowAuthenticationRequirement.REQUIRE_AUTHENTICATED
        self.target_flow.save()
        self.stage.mode = RedirectMode.FLOW
        self.stage.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(response, component="ak-stage-access-denied")

    def test_serializer(self):
        with self.assertRaises(ValidationError):
            RedirectStageSerializer(
                data={
                    "name": generate_id(20),
                    "mode": RedirectMode.STATIC,
                }
            ).is_valid(raise_exception=True)

        self.assertTrue(
            RedirectStageSerializer(
                data={
                    "name": generate_id(20),
                    "mode": RedirectMode.STATIC,
                    "target_static": URL,
                }
            ).is_valid(raise_exception=True)
        )

        with self.assertRaises(ValidationError):
            RedirectStageSerializer(
                data={
                    "name": generate_id(20),
                    "mode": RedirectMode.FLOW,
                }
            ).is_valid(raise_exception=True)

        self.assertTrue(
            RedirectStageSerializer(
                data={
                    "name": generate_id(20),
                    "mode": RedirectMode.FLOW,
                    "target_flow": create_test_flow().flow_uuid,
                }
            ).is_valid(raise_exception=True)
        )
