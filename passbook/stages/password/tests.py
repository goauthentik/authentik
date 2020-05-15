"""password tests"""
import string
from random import SystemRandom
from unittest.mock import MagicMock, patch

from django.core.exceptions import PermissionDenied
from django.shortcuts import reverse
from django.test import Client, TestCase

from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.password.models import PasswordStage

MOCK_BACKEND_AUTHENTICATE = MagicMock(side_effect=PermissionDenied("test"))


class TestPasswordStage(TestCase):
    """Password tests"""

    def setUp(self):
        super().setUp()
        self.password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )
        self.user = User.objects.create_user(
            username="unittest", email="test@beryju.org", password=self.password
        )
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-password",
            slug="test-password",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = PasswordStage.objects.create(
            name="password", backends=["django.contrib.auth.backends.ModelBackend"]
        )
        FlowStageBinding.objects.create(flow=self.flow, stage=self.stage, order=2)

    def test_without_user(self):
        """Test without user"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            # Still have to send the password so the form is valid
            {"password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_flows:denied"))

    def test_recovery_flow_link(self):
        """Test link to the default recovery flow"""
        flow = Flow.objects.create(
            designation=FlowDesignation.RECOVERY, slug="qewrqerqr"
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(flow.slug, response.rendered_content)

    def test_valid_password(self):
        """Test with a valid pending user and valid password"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            # Form data
            {"password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_core:overview"))

    def test_invalid_password(self):
        """Test with a valid pending user and invalid password"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            # Form data
            {"password": self.password + "test"},
        )
        self.assertEqual(response.status_code, 200)

    @patch(
        "django.contrib.auth.backends.ModelBackend.authenticate",
        MOCK_BACKEND_AUTHENTICATE,
    )
    def test_permission_denied(self):
        """Test with a valid pending user and valid password.
        Backend is patched to return PermissionError"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            # Form data
            {"password": self.password + "test"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_flows:denied"))
