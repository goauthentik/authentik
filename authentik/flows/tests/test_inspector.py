"""Flow inspector tests"""

from json import loads

from django.test.client import RequestFactory
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding, InvalidResponseAction
from authentik.lib.generators import generate_id
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
        flow = Flow.objects.create(
            name=generate_id(),
            slug=generate_id(),
            designation=FlowDesignation.AUTHENTICATION,
        )

        # Stage 1 is an identification stage
        ident_stage = IdentificationStage.objects.create(
            name="ident",
            user_fields=[UserFields.USERNAME],
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=ident_stage,
            order=1,
            invalid_response_action=InvalidResponseAction.RESTART_WITH_CONTEXT,
        )
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy2"), order=1
        )

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertJSONEqual(
            res.content,
            {
                "component": "ak-stage-identification",
                "flow_info": {
                    "background": flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": "",
                    "layout": "stacked",
                },
                "type": ChallengeTypes.NATIVE.value,
                "password_fields": False,
                "primary_action": "Log in",
                "sources": [],
                "show_source_labels": False,
                "user_fields": ["username"],
            },
        )

        ins = self.client.get(
            reverse("authentik_api:flow-inspector", kwargs={"flow_slug": flow.slug}),
        )
        content = loads(ins.content)
        self.assertEqual(content["is_completed"], False)
        self.assertEqual(content["current_plan"]["current_stage"]["stage_obj"]["name"], "ident")
        self.assertEqual(
            content["current_plan"]["next_planned_stage"]["stage_obj"]["name"], "dummy2"
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
        self.assertEqual(content["plans"][0]["current_stage"]["stage_obj"]["name"], "ident")
        self.assertEqual(content["current_plan"]["current_stage"]["stage_obj"]["name"], "dummy2")
        self.assertEqual(
            content["current_plan"]["plan_context"]["pending_user"]["username"], self.admin.username
        )
