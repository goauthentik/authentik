"""write tests"""
import string
from random import SystemRandom
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests.test_views import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from authentik.stages.user_write.forms import UserWriteStageForm
from authentik.stages.user_write.models import UserWriteStage


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
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_user_create(self):
        """Test creation of user"""
        password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )

        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
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
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"to": reverse("authentik_core:root-redirect"), "type": "redirect"},
        )
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
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = User.objects.create(
            username="unittest", email="test@beryju.org"
        )
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "test-user-new",
            "password": new_password,
            "attribute_some-custom-attribute": "test",
            "some_ignored_attribute": "bar",
        }
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"to": reverse("authentik_core:root-redirect"), "type": "redirect"},
        )
        user_qs = User.objects.filter(
            username=plan.context[PLAN_CONTEXT_PROMPT]["username"]
        )
        self.assertTrue(user_qs.exists())
        self.assertTrue(user_qs.first().check_password(new_password))
        self.assertEqual(user_qs.first().attributes["some-custom-attribute"], "test")
        self.assertNotIn("some_ignored_attribute", user_qs.first().attributes)

    @patch(
        "authentik.flows.views.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_without_data(self):
        """Test without data results in error"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "ak-stage-access-denied",
                "error_message": None,
                "title": "",
                "type": ChallengeTypes.native.value,
            },
        )

    def test_form(self):
        """Test Form"""
        data = {"name": "test"}
        self.assertEqual(UserWriteStageForm(data).is_valid(), True)
