from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.endpoints.models import Device, EndpointStage, StageMode
from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id


class TestGoogleChromeStage(FlowTestCase):
    def setUp(self):
        self.connector = GoogleChromeConnector.objects.create(
            name=generate_id(),
            credentials={},
        )

    def _setup_flow(self, mode: StageMode) -> str:
        self.flow = create_test_flow()
        self.stage = EndpointStage.objects.create(
            name=generate_id(),
            connector=self.connector,
            mode=mode,
        )
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)
        return reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})

    def test_endpoint_stage_optional(self):
        """OPTIONAL: the stage continues even when no device was verified."""
        url = self._setup_flow(StageMode.OPTIONAL)

        res = self.client.get(url)
        self.assertStageResponse(res, flow=self.flow, component="xak-flow-frame")

        with self.assertFlowFinishes() as plan:
            res = self.client.post(url, data={})
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        plan = plan()
        self.assertNotIn(PLAN_CONTEXT_DEVICE, plan.context)

    def test_endpoint_stage_required_none(self):
        """REQUIRED: a response without a verified device is denied."""
        url = self._setup_flow(StageMode.REQUIRED)

        res = self.client.get(url)
        self.assertStageResponse(res, flow=self.flow, component="xak-flow-frame")

        res = self.client.post(url, data={})
        self.assertStageResponse(
            res,
            flow=self.flow,
            component="ak-stage-access-denied",
            error_message="Invalid challenge response",
        )
        self.assertEqual(Device.objects.count(), 0)

    def test_endpoint_stage_required_with_device(self):
        """REQUIRED: once the iframe records a verified device, the stage continues."""
        url = self._setup_flow(StageMode.REQUIRED)

        res = self.client.get(url)
        self.assertStageResponse(res, flow=self.flow, component="xak-flow-frame")

        # Simulate the Verified-Access iframe having written the verified device
        # into the plan context (see views/dtc.py).
        device = Device.objects.create(identifier=generate_id())
        plan = self.get_flow_plan()
        plan.context[PLAN_CONTEXT_DEVICE] = device
        self.set_flow_plan(plan)

        with self.assertFlowFinishes() as plan:
            res = self.client.post(url, data={})
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        plan = plan()
        self.assertEqual(plan.context[PLAN_CONTEXT_DEVICE], device)
