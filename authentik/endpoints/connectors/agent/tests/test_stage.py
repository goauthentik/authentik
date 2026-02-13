from hashlib import sha256
from json import loads

from django.urls import reverse
from jwt import encode

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    DeviceAuthenticationToken,
    DeviceToken,
    EnrollmentToken,
)
from authentik.endpoints.connectors.agent.stage import (
    PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE,
    PLAN_CONTEXT_DEVICE_AUTH_TOKEN,
)
from authentik.endpoints.models import Device, EndpointStage, StageMode
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id


class TestEndpointStage(FlowTestCase):

    def setUp(self):
        cert = create_test_cert()
        self.connector = AgentConnector.objects.create(name=generate_id(), challenge_key=cert)
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.device = Device.objects.create(
            identifier=generate_id(),
        )
        self.connection = AgentDeviceConnection.objects.create(
            device=self.device,
            connector=self.connector,
        )
        self.device_token = DeviceToken.objects.create(
            device=self.connection,
            key=generate_id(),
        )
        self.device_auth_token = DeviceAuthenticationToken.objects.create(
            device=self.device,
            device_token=self.device_token,
            connector=self.connector,
        )

    def test_endpoint_stage(self):
        flow = create_test_flow()
        stage = EndpointStage.objects.create(connector=self.connector)
        FlowStageBinding.objects.create(stage=stage, target=flow, order=0)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageResponse(res, flow=flow, component="ak-stage-endpoint-agent")

        challenge = loads(res.content.decode())["challenge"]

        DeviceToken.objects.create(
            device=self.connection,
            key=generate_id(),
        )

        response = encode(
            {
                "iss": self.device.identifier,
                "atc": challenge,
                "aud": "goauthentik.io/platform/endpoint",
            },
            key=self.device_token.key,
            algorithm="HS512",
        )

        with self.assertFlowFinishes() as plan:
            res = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                data={"component": "ak-stage-endpoint-agent", "response": response},
            )
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        plan = plan()
        self.assertNotIn(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE, plan.context)
        self.assertEqual(plan.context[PLAN_CONTEXT_DEVICE], self.device)

    def test_endpoint_stage_optional(self):
        flow = create_test_flow()
        stage = EndpointStage.objects.create(connector=self.connector, mode=StageMode.OPTIONAL)
        FlowStageBinding.objects.create(stage=stage, target=flow, order=0)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageResponse(res, flow=flow, component="ak-stage-endpoint-agent")

        challenge = loads(res.content.decode())["challenge"]

        response = encode(
            {
                "iss": self.device.identifier,
                "atc": challenge,
                "aud": "goauthentik.io/platform/endpoint",
            },
            key=self.device_token.key,
            algorithm="HS512",
        )

        with self.assertFlowFinishes() as plan:
            res = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                data={"component": "ak-stage-endpoint-agent", "response": response},
            )
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        plan = plan()
        self.assertNotIn(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE, plan.context)
        self.assertEqual(plan.context[PLAN_CONTEXT_DEVICE], self.device)

    def test_endpoint_stage_optional_none(self):
        flow = create_test_flow()
        stage = EndpointStage.objects.create(connector=self.connector, mode=StageMode.OPTIONAL)
        FlowStageBinding.objects.create(stage=stage, target=flow, order=0)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageResponse(res, flow=flow, component="ak-stage-endpoint-agent")

        with self.assertFlowFinishes() as plan:
            res = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                data={"component": "ak-stage-endpoint-agent", "response": None},
            )
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        plan = plan()
        self.assertNotIn(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE, plan.context)
        self.assertNotIn(PLAN_CONTEXT_DEVICE, plan.context)

    def test_endpoint_stage_optional_invalid(self):
        flow = create_test_flow()
        stage = EndpointStage.objects.create(connector=self.connector, mode=StageMode.OPTIONAL)
        FlowStageBinding.objects.create(stage=stage, target=flow, order=0)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageResponse(res, flow=flow, component="ak-stage-endpoint-agent")

        with self.assertFlowFinishes() as plan:
            res = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                data={"component": "ak-stage-endpoint-agent", "response": generate_id()},
            )
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        plan = plan()
        self.assertNotIn(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE, plan.context)
        self.assertNotIn(PLAN_CONTEXT_DEVICE, plan.context)

    def test_endpoint_stage_required_none(self):
        flow = create_test_flow()
        stage = EndpointStage.objects.create(connector=self.connector, mode=StageMode.REQUIRED)
        FlowStageBinding.objects.create(stage=stage, target=flow, order=0)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageResponse(res, flow=flow, component="ak-stage-endpoint-agent")

        res = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            data={"component": "ak-stage-endpoint-agent", "response": None},
        )
        self.assertStageResponse(
            res,
            flow=flow,
            component="ak-stage-access-denied",
            error_message="Invalid challenge response",
        )

    def test_endpoint_stage_required_invalid(self):
        flow = create_test_flow()
        stage = EndpointStage.objects.create(connector=self.connector, mode=StageMode.REQUIRED)
        FlowStageBinding.objects.create(stage=stage, target=flow, order=0)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(res.status_code, 200)
        self.assertStageResponse(res, flow=flow, component="ak-stage-endpoint-agent")

        res = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            data={"component": "ak-stage-endpoint-agent", "response": generate_id()},
        )
        self.assertStageResponse(
            res,
            flow=flow,
            component="ak-stage-endpoint-agent",
            response_errors={
                "response": [{"string": "Invalid challenge response", "code": "invalid"}]
            },
        )

    def test_endpoint_stage_ia_dth(self):
        """Test with DTH"""
        flow = create_test_flow()
        stage = EndpointStage.objects.create(connector=self.connector)
        FlowStageBinding.objects.create(stage=stage, target=flow, order=0)

        # Send an "invalid" request first, to populate the flow plan
        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        plan = self.get_flow_plan()
        plan.context[PLAN_CONTEXT_DEVICE_AUTH_TOKEN] = DeviceAuthenticationToken.objects.get(
            pk=self.device_auth_token.pk
        )
        self.set_flow_plan(plan)

        with self.assertFlowFinishes() as plan:
            res = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                HTTP_X_AUTHENTIK_PLATFORM_AUTH_DTH=sha256(
                    self.device_token.key.encode()
                ).hexdigest(),
            )
            self.assertStageRedirects(res, reverse("authentik_core:root-redirect"))
        plan = plan()
        self.assertNotIn(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE, plan.context)
        self.assertEqual(plan.context[PLAN_CONTEXT_DEVICE], self.device)
