"""create tests"""
import string
from random import SystemRandom

from django.shortcuts import reverse
from django.test import Client, TestCase

from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from passbook.stages.user_create.models import UserCreateStage


class TestUserCreateStage(TestCase):
    """Create tests"""

    def setUp(self):
        super().setUp()
        self.client = Client()

        self.password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )
        self.flow = Flow.objects.create(
            name="test-create",
            slug="test-create",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = UserCreateStage.objects.create(name="create")
        FlowStageBinding.objects.create(flow=self.flow, stage=self.stage, order=2)

    def test_valid_create(self):
        """Test creation of user"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "test-user",
            "name": "name",
            "email": "test@beryju.org",
            "password": self.password,
        }
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            User.objects.filter(
                username=plan.context[PLAN_CONTEXT_PROMPT]["username"]
            ).exists()
        )

    def test_without_data(self):
        """Test without data results in error"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_flows:denied"))
