"""write tests"""
import string
from random import SystemRandom

from django.shortcuts import reverse
from django.test import Client, TestCase

from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from passbook.stages.user_write.forms import UserWriteStageForm
from passbook.stages.user_write.models import UserWriteStage


class TestUserWriteStage(TestCase):
    """Write tests"""

    def setUp(self):
        super().setUp()
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-write",
            slug="test-write",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = UserWriteStage.objects.create(name="write")
        FlowStageBinding.objects.create(flow=self.flow, stage=self.stage, order=2)

    def test_user_create(self):
        """Test creation of user"""
        password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "test-user",
            "name": "name",
            "email": "test@beryju.org",
            "password": password,
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
        user_qs = User.objects.filter(
            username=plan.context[PLAN_CONTEXT_PROMPT]["username"]
        )
        self.assertTrue(user_qs.exists())
        self.assertTrue(user_qs.first().check_password(password))

    def test_user_update(self):
        """Test update of existing user"""
        new_password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )
        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        plan.context[PLAN_CONTEXT_PENDING_USER] = User.objects.create(
            username="unittest", email="test@beryju.org"
        )
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "test-user-new",
            "password": new_password,
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
        user_qs = User.objects.filter(
            username=plan.context[PLAN_CONTEXT_PROMPT]["username"]
        )
        self.assertTrue(user_qs.exists())
        self.assertTrue(user_qs.first().check_password(new_password))

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

    def test_form(self):
        """Test Form"""
        data = {"name": "test"}
        self.assertEqual(UserWriteStageForm(data).is_valid(), True)
