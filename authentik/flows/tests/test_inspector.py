"""Flow inspector tests"""

from json import loads

from django.test.client import RequestFactory
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding, InvalidResponseAction
from authentik.flows.planner import PLAN_CONTEXT_POLICY_RESULTS
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.dummy.models import DummyStage
from authentik.stages.identification.models import IdentificationStage, UserFields


class TestFlowInspector(APITestCase):
    """Test inspector"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.admin = create_test_admin_user()
        self.client.force_login(self.admin)

    def test(self):
        """test inspector"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)

        # Stage 1 is an identification stage
        ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[UserFields.USERNAME],
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=ident_stage,
            order=0,
            invalid_response_action=InvalidResponseAction.RESTART_WITH_CONTEXT,
        )
        dummy_stage = DummyStage.objects.create(name=generate_id())
        FlowStageBinding.objects.create(target=flow, stage=dummy_stage, order=1)
        policy = ExpressionPolicy.objects.create(
            name=generate_id(), expression='return {"risk": 7}'
        )
        policy_binding = PolicyBinding.objects.create(target=flow, policy=policy, order=0)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertJSONEqual(
            res.content,
            {
                "allow_show_password": False,
                "captcha_stage": None,
                "component": "ak-stage-identification",
                "enable_remember_me": False,
                "flow_info": {
                    "background": "/static/dist/assets/images/flow_background.jpg",
                    "background_themed_urls": None,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": flow.title,
                    "layout": "stacked",
                    "messages": [],
                },
                "flow_designation": "authentication",
                "passkey_challenge": None,
                "password_fields": False,
                "primary_action": "Log in",
                "sources": [],
                "show_source_labels": False,
                "pending_user_identifier": None,
                "user_fields": ["username"],
            },
        )

        ins = self.client.get(
            reverse("authentik_api:flow-inspector", kwargs={"flow_slug": flow.slug}),
        )
        content = loads(ins.content)
        self.assertEqual(content["is_completed"], False)
        self.assertEqual(
            content["current_plan"]["current_stage"]["stage_obj"]["name"], ident_stage.name
        )
        self.assertEqual(
            content["current_plan"]["next_planned_stage"]["stage_obj"]["name"], dummy_stage.name
        )
        self.assertEqual(
            content["current_plan"]["plan_context"][PLAN_CONTEXT_POLICY_RESULTS][
                str(policy_binding.pk)
            ],
            {
                "policy": policy.name,
                "passing": True,
                "messages": [],
                "raw_result": {"risk": 7},
            },
        )

        self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.admin.username},
            follow=True,
        )

        ins = self.client.get(
            reverse("authentik_api:flow-inspector", kwargs={"flow_slug": flow.slug}),
        )
        content = loads(ins.content)
        self.assertEqual(content["is_completed"], False)
        self.assertEqual(
            content["plans"][0]["current_stage"]["stage_obj"]["name"], ident_stage.name
        )
        self.assertEqual(
            content["current_plan"]["current_stage"]["stage_obj"]["name"], dummy_stage.name
        )
        self.assertEqual(
            content["current_plan"]["plan_context"]["pending_user"]["username"], self.admin.username
        )

    def test_completed_runtime_policy_result(self):
        """Inspector retains a runtime policy result that skips the final stage."""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stage_binding = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=0,
            evaluate_on_plan=False,
            re_evaluate_policies=True,
        )
        policy = DummyPolicy.objects.create(
            name=generate_id(), result=False, wait_min=0, wait_max=1
        )
        policy_binding = PolicyBinding.objects.create(target=stage_binding, policy=policy, order=0)

        self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        response = self.client.get(
            reverse("authentik_api:flow-inspector", kwargs={"flow_slug": flow.slug}),
        )

        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["is_completed"], True)
        self.assertEqual(
            content["current_plan"]["plan_context"][PLAN_CONTEXT_POLICY_RESULTS][
                str(policy_binding.pk)
            ],
            {
                "policy": policy.name,
                "passing": False,
                "messages": ["dummy"],
                "raw_result": None,
            },
        )
