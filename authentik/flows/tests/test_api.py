"""API flow tests"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.api.stages import StageSerializer, StageViewSet
from authentik.flows.models import (
    Flow,
    FlowAuthenticationRequirement,
    FlowDesignation,
    FlowStageBinding,
    Stage,
)
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.dummy.models import DummyStage


def nodes_by_identifier(graph: dict) -> dict[str, dict]:
    """Index a diagram graph's nodes by their identifier."""
    return {node["identifier"]: node for node in graph["nodes"]}


def edge_set(graph: dict) -> set[tuple[str, str, str]]:
    return {(edge["origin"], edge["target"], edge["type"]) for edge in graph["edges"]}


class TestFlowsAPI(APITestCase):
    """API tests"""

    def test_models(self):
        self.assertIsNone(Stage().ui_user_settings())

    def test_api_serializer(self):
        obj = DummyStage()
        self.assertEqual(StageSerializer().get_component(obj), "ak-stage-dummy-form")
        self.assertEqual(StageSerializer().get_verbose_name(obj), "Dummy Stage")

    def test_api_viewset(self):
        dummy = DummyStage.objects.create()
        self.assertIn(dummy, StageViewSet().get_queryset())

    def diagram_flow(self, **kwargs) -> Flow:
        self.client.force_login(create_test_admin_user())
        return Flow.objects.create(
            name="test-default-context",
            slug="test-default-context",
            designation=FlowDesignation.AUTHENTICATION,
            **kwargs,
        )

    def diagram(self, flow: Flow) -> dict:
        """Test flow diagram."""
        response = self.client.get(
            reverse("authentik_api:flow-diagram", kwargs={"slug": flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        return loads(response.content)

    def policy(self, target, name: str, order: int = 0) -> PolicyBinding:
        return PolicyBinding.objects.create(
            policy=DummyPolicy.objects.create(name=name, result=False, wait_min=1, wait_max=2),
            target=target,
            order=order,
        )

    def test_api_diagram_stage_carries_stage_and_binding_identity(self):
        flow = self.diagram_flow()
        stage = DummyStage.objects.create(name="dummy1")
        binding = FlowStageBinding.objects.create(target=flow, stage=stage, order=0)

        node = nodes_by_identifier(self.diagram(flow))["stage_0"]

        self.assertEqual(node["type"], "stage")
        self.assertEqual(node["name"], "dummy1")
        self.assertEqual(node["verbose_name"], "Dummy Stage")
        self.assertEqual(node["model"], "authentik_stages_dummy.dummystage")
        self.assertEqual(node["pk"], str(stage.pk))
        self.assertEqual(node["component"], "ak-stage-dummy-form")
        self.assertEqual(node["binding_model"], "authentik_flows.flowstagebinding")
        self.assertEqual(node["binding_pk"], str(binding.pk))
        self.assertEqual(node["binding_order"], 0)

    def test_api_diagram_policy_carries_policy_and_binding_identity(self):
        flow = self.diagram_flow()
        binding = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy1"), order=0
        )
        policy_binding = self.policy(binding, "dummy1-policy", order=3)

        node = nodes_by_identifier(self.diagram(flow))["stage_0_policy_0"]

        self.assertEqual(node["type"], "policy")
        self.assertEqual(node["name"], "dummy1-policy")
        self.assertEqual(node["verbose_name"], "Dummy Policy")
        self.assertEqual(node["model"], "authentik_policies_dummy.dummypolicy")
        self.assertEqual(node["pk"], str(policy_binding.policy.pk))
        self.assertEqual(node["component"], "ak-policy-dummy-form")
        self.assertEqual(node["binding_model"], "authentik_policies.policybinding")
        self.assertEqual(node["binding_pk"], str(policy_binding.pk))
        self.assertEqual(node["binding_order"], 3)

    def test_api_diagram_stage_with_bound_policies_works(self):
        flow = self.diagram_flow()
        for order, name in enumerate(("dummy1", "dummy2", "dummy3")):
            binding = FlowStageBinding.objects.create(
                target=flow,
                stage=DummyStage.objects.create(name=name),
                order=order,
            )
            if order == 1:
                self.policy(binding, "dummy2-policy")

        self.assertEqual(
            edge_set(self.diagram(flow)),
            {
                ("flow_start", "stage_0", "proceed"),
                ("stage_0", "stage_1_policy_0", "proceed"),
                ("stage_1_policy_0", "stage_1", "policy-passed"),
                ("stage_1", "stage_2", "proceed"),
                ("stage_1_policy_0", "stage_2", "policy-denied"),
                ("stage_2", "done", "proceed"),
            },
        )

    def test_api_diagram_declares_each_node_once(self):
        flow = self.diagram_flow()
        for order, name in enumerate(("dummy1", "dummy2")):
            binding = FlowStageBinding.objects.create(
                target=flow,
                stage=DummyStage.objects.create(name=name),
                order=order,
            )
            if order == 0:
                self.policy(binding, "dummy1-policy")

        identifiers = [node["identifier"] for node in self.diagram(flow)["nodes"]]

        self.assertCountEqual(identifiers, set(identifiers))

    def test_api_diagram_flow_policies_control_entry(self):
        flow = self.diagram_flow()
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy1"), order=0
        )
        policy_binding = self.policy(flow, "flow-policy", order=2)

        graph = self.diagram(flow)
        nodes = nodes_by_identifier(graph)

        self.assertEqual(nodes["flow_pre"]["type"], "pre-flow-policies")
        self.assertEqual(nodes["flow_policy_0"]["binding_pk"], str(policy_binding.pk))
        self.assertEqual(nodes["flow_policy_0"]["binding_order"], 2)
        self.assertEqual(
            edge_set(graph),
            {
                ("flow_pre", "flow_policy_0", "binding"),
                ("flow_policy_0", "done", "policy-denied"),
                ("flow_policy_0", "flow_start", "proceed"),
                ("flow_start", "stage_0", "proceed"),
                ("stage_0", "done", "proceed"),
            },
        )

    def test_api_diagram_auth_requirement_controls_entry(self):
        flow = self.diagram_flow(authentication=FlowAuthenticationRequirement.REQUIRE_AUTHENTICATED)
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy1"), order=0
        )

        graph = self.diagram(flow)
        node = nodes_by_identifier(graph)["flow_auth_requirement"]

        self.assertEqual(node["type"], "authentication-requirement")
        self.assertEqual(node["name"], "require_authenticated")

        # The old emitter declared `flow_start` a second time, labelled
        # "placeholder", purely to draw the fulfilled edge.
        self.assertNotIn("placeholder", [n["name"] for n in graph["nodes"]])
        self.assertEqual(
            edge_set(graph),
            {
                ("flow_auth_requirement", "done", "requirement-unfulfilled"),
                (
                    "flow_auth_requirement",
                    "flow_start",
                    "requirement-fulfilled",
                ),
                ("flow_start", "stage_0", "proceed"),
                ("stage_0", "done", "proceed"),
            },
        )

    def test_api_background(self):
        user = create_test_admin_user()
        self.client.force_login(user)

        flow = create_test_flow()
        response = self.client.get(reverse("authentik_api:flow-detail", kwargs={"slug": flow.slug}))
        body = loads(response.content.decode())
        self.assertEqual(
            body["background_url"],
            "/static/dist/assets/images/flow_background.jpg",
        )

        flow.background = "https://goauthentik.io/img/icon.png"
        flow.save()
        response = self.client.get(reverse("authentik_api:flow-detail", kwargs={"slug": flow.slug}))
        body = loads(response.content.decode())
        self.assertEqual(body["background"], "https://goauthentik.io/img/icon.png")

    def test_api_diagram_no_stages(self):
        """Test flow diagram with no stages."""
        flow = self.diagram_flow()

        graph = self.diagram(flow)

        self.assertEqual(
            [node["identifier"] for node in graph["nodes"]],
            ["flow_start", "done"],
        )
        self.assertEqual(
            nodes_by_identifier(graph)["flow_start"]["name"],
            "test-default-context",
        )
        self.assertEqual(edge_set(graph), {("flow_start", "done", "proceed")})

    def test_types(self):
        """Test Stage's types endpoint"""
        user = create_test_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("authentik_api:stage-types"),
        )
        self.assertEqual(response.status_code, 200)

    def test_execute(self):
        """Test execute endpoint"""
        user = create_test_admin_user()
        self.client.force_login(user)

        flow = Flow.objects.create(
            name=generate_id(),
            slug=generate_id(),
            designation=FlowDesignation.AUTHENTICATION,
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=0,
        )
        response = self.client.get(
            reverse("authentik_api:flow-execute", kwargs={"slug": flow.slug})
        )
        self.assertEqual(response.status_code, 200)
