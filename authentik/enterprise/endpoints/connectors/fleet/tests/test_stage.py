from json import loads
from ssl import PEM_FOOTER, PEM_HEADER

from django.urls import reverse
from requests_mock import Mocker

from authentik.core.tests.utils import (
    create_test_flow,
)
from authentik.endpoints.models import Device, EndpointStage, StageMode
from authentik.enterprise.endpoints.connectors.fleet.models import FleetConnector
from authentik.enterprise.stages.mtls.stage import PLAN_CONTEXT_CERTIFICATE
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


class FleetConnectorStageTests(FlowTestCase):
    def setUp(self):
        super().setUp()
        self.connector = FleetConnector.objects.create(
            name=generate_id(), url="http://localhost", token=generate_id()
        )

        controller = self.connector.controller(self.connector)
        with Mocker() as mock:
            mock.get(
                "http://localhost/api/v1/fleet/conditional_access/idp/apple/profile",
                text=load_fixture("fixtures/cond_acc_profile.mobileconfig"),
            )
            mock.get(
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=0&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json={"hosts": [loads(load_fixture("fixtures/host_macos.json"))]},
            )
            mock.get(
                "http://localhost/api/v1/fleet/hosts?order_key=hardware_serial&page=1&per_page=50&device_mapping=true&populate_software=true&populate_users=true",
                json={"hosts": []},
            )
            controller.sync_endpoints()

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = EndpointStage.objects.create(
            name=generate_id(),
            mode=StageMode.REQUIRED,
            connector=self.connector,
        )

        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)

        self.host_cert = load_fixture("fixtures/cond_acc_host.pem")

    def _format_traefik(self, cert: str | None = None):
        cert = cert if cert else self.host_cert
        return cert.replace(PEM_HEADER, "").replace(PEM_FOOTER, "").replace("\n", "")

    def test_assoc(self):
        dev = Device.objects.get(identifier="ZV35VFDD50")
        with self.assertFlowFinishes() as plan:
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                headers={"X-Forwarded-TLS-Client-Cert": self._format_traefik()},
            )
            self.assertEqual(res.status_code, 200)
        plan = plan()
        self.assertEqual(plan.context[PLAN_CONTEXT_DEVICE], dev)
        self.assertEqual(
            plan.context[PLAN_CONTEXT_CERTIFICATE]["subject"],
            "CN=Fleet conditional access for Okta",
        )

    def test_assoc_not_found(self):
        dev = Device.objects.get(identifier="ZV35VFDD50")
        dev.delete()
        with self.assertFlowFinishes() as plan:
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                headers={"X-Forwarded-TLS-Client-Cert": self._format_traefik()},
            )
            self.assertEqual(res.status_code, 200)
            self.assertStageResponse(res, self.flow, component="ak-stage-access-denied")
        plan = plan()
        self.assertNotIn(PLAN_CONTEXT_DEVICE, plan.context)
