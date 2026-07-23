from django.db.models.deletion import ProtectedError
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.enterprise.stages.authenticator_endpoint_gdtc.models import (
    AuthenticatorEndpointGDTCStage,
    EndpointDevice,
    EndpointDeviceConnection,
)
from authentik.enterprise.stages.authenticator_endpoint_gdtc.views.dtc import (
    PLAN_CONTEXT_METHOD_ARGS_ENDPOINTS,
)
from authentik.flows.models import FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD_ARGS


class TestAuthenticatorEndpointGDTCStage(FlowTestCase):
    def setUp(self):
        self.user = create_test_admin_user()
        self.flow = create_test_flow()
        self.stage = AuthenticatorEndpointGDTCStage.objects.create(
            name=generate_id(),
            credentials={},
        )
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)
        self.url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})

    def test_stage_deletion_is_protected(self):
        """A setup stage with an endpoint connection cannot be deleted."""
        device = EndpointDevice.objects.create(
            name=generate_id(),
            host_identifier=generate_id(),
            user=self.user,
            data={},
        )
        connection = EndpointDeviceConnection.objects.create(
            device=device,
            stage=self.stage,
            attributes={},
        )

        with self.assertRaises(ProtectedError):
            self.stage.delete()

        self.assertTrue(AuthenticatorEndpointGDTCStage.objects.filter(pk=self.stage.pk).exists())
        self.assertTrue(EndpointDeviceConnection.objects.filter(pk=connection.pk).exists())
        self.assertTrue(EndpointDevice.objects.filter(pk=device.pk).exists())

    def test_bypass_blocked(self):
        """A POST that skips the Verified-Access iframe must not advance the flow."""
        res = self.client.get(self.url)
        self.assertStageResponse(res, flow=self.flow, component="xak-flow-frame")

        # No verification recorded in the plan context -> the stage re-renders the
        # frame challenge instead of continuing.
        res = self.client.post(self.url, data={})
        self.assertStageResponse(res, flow=self.flow, component="xak-flow-frame")

    def test_verified_continues(self):
        """Once the iframe records a verified endpoint, the flow continues."""
        res = self.client.get(self.url)
        self.assertStageResponse(res, flow=self.flow, component="xak-flow-frame")

        # Simulate the iframe (views/dtc.py) having recorded the verified endpoint.
        plan = self.get_flow_plan()
        plan.context[PLAN_CONTEXT_METHOD_ARGS] = {
            PLAN_CONTEXT_METHOD_ARGS_ENDPOINTS: [{"deviceSignals": {"serialNumber": generate_id()}}]
        }
        self.set_flow_plan(plan)

        with self.assertFlowFinishes():
            res = self.client.post(self.url, data={})
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
