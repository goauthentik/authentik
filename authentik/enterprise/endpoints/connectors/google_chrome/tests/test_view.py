from json import dumps
from unittest.mock import MagicMock, patch

from django.urls import reverse

from authentik.core.tests.utils import RequestFactory, create_test_flow
from authentik.endpoints.models import Device, EndpointStage
from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector
from authentik.enterprise.providers.google_workspace.clients.test_http import MockHTTP
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


class TestChromeDTCView(FlowTestCase):
    def setUp(self):
        self.flow = create_test_flow()
        self.connector = GoogleChromeConnector.objects.create(
            name=generate_id(),
            credentials={},
        )
        self.factory = RequestFactory()
        self.api_key = generate_id()
        self.stage = EndpointStage.objects.create(
            name=generate_id(),
            connector=self.connector,
        )
        FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )

    def test_dtc_generate_verify(self):
        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            res,
            self.flow,
            component="xak-flow-frame",
            url="http://testserver/endpoints/google/chrome/",
        )

        challenge = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://verifiedaccess.googleapis.com/v2/challenge:generate?key={self.api_key}&alt=json",
            {"challenge": challenge},
            method="POST",
        )
        http.add_response(
            f"https://verifiedaccess.googleapis.com/v2/challenge:verify?key={self.api_key}&alt=json",
            load_fixture("fixtures/host_macos.json"),
            method="POST",
        )
        with patch(
            "authentik.enterprise.endpoints.connectors.google_chrome.models.GoogleChromeConnector.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            # Generate challenge
            res = self.client.get(
                reverse("authentik_endpoints_connectors_google_chrome:chrome"),
                HTTP_X_DEVICE_TRUST="VerifiedAccess",
            )
            self.assertEqual(res.status_code, 302)
            self.assertEqual(
                res.headers["X-Verified-Access-Challenge"],
                dumps({"challenge": challenge}),
            )

            # Validate challenge
            res = self.client.get(
                reverse("authentik_endpoints_connectors_google_chrome:chrome"),
                HTTP_X_VERIFIED_ACCESS_CHALLENGE_RESPONSE=dumps({}),
            )
            self.assertEqual(res.status_code, 200)
        device = Device.objects.get(identifier="Z5DDF07GK6")
        self.assertIsNotNone(device)

        # Continue flow
        with self.assertFlowFinishes() as plan:
            res = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            )
            self.assertStageRedirects(res, "/")
        plan = plan()
        plan_device = plan.context[PLAN_CONTEXT_DEVICE]
        self.assertEqual(device.pk, plan_device.pk)
