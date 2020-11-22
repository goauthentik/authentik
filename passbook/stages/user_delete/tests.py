"""delete tests"""
from unittest.mock import patch

from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils.encoding import force_str

from passbook.core.models import User
from passbook.flows.markers import StageMarker
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.flows.tests.test_views import TO_STAGE_RESPONSE_MOCK
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.policies.http import AccessDeniedResponse
from passbook.stages.user_delete.models import UserDeleteStage


class TestUserDeleteStage(TestCase):
    """Delete tests"""

    def setUp(self):
        super().setUp()
        self.username = "qerqwerqrwqwerwq"
        self.user = User.objects.create(username=self.username, email="test@beryju.org")
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-delete",
            slug="test-delete",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = UserDeleteStage.objects.create(name="delete")
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    @patch(
        "passbook.flows.views.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_no_user(self):
        """Test without user set"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, AccessDeniedResponse)

    def test_user_delete_get(self):
        """Test Form render"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_user_delete_post(self):
        """Test User delete (actual)"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            {},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"type": "redirect", "to": reverse("passbook_core:shell")},
        )

        self.assertFalse(User.objects.filter(username=self.username).exists())
