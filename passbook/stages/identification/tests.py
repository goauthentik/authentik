"""identification tests"""
from django.shortcuts import reverse
from django.test import Client, TestCase

from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.sources.oauth.models import OAuthSource
from passbook.stages.identification.models import (
    IdentificationStage,
    Templates,
    UserFields,
)


class TestIdentificationStage(TestCase):
    """Identification tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-identification",
            slug="test-identification",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = IdentificationStage.objects.create(
            name="identification",
            user_fields=[UserFields.E_MAIL],
            template=Templates.DEFAULT_LOGIN,
        )
        FlowStageBinding.objects.create(
            flow=self.flow, stage=self.stage, order=0,
        )

        # OAuthSource for the login view
        OAuthSource.objects.create(name="test", slug="test")

    def test_valid_render(self):
        """Test that View renders correctly"""
        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_valid_with_email(self):
        """Test with valid email, check that URL redirects back to itself"""
        form_data = {"uid_field": self.user.email}
        url = reverse(
            "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
        )
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_core:overview"))

    def test_invalid_with_username(self):
        """Test invalid with username (user exists but stage only allows e-mail)"""
        form_data = {"uid_field": self.user.username}
        response = self.client.post(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            form_data,
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_with_invalid_email(self):
        """Test with invalid e-mail (user doesn't exist) -> Will return to login form"""
        form_data = {"uid_field": self.user.email + "test"}
        response = self.client.post(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            form_data,
        )
        self.assertEqual(response.status_code, 200)

    def test_enrollment_flow(self):
        """Test that enrollment flow is linked correctly"""
        flow = Flow.objects.create(
            name="enroll-test",
            slug="unique-enrollment-string",
            designation=FlowDesignation.ENROLLMENT,
        )
        FlowStageBinding.objects.create(
            flow=flow, stage=self.stage, order=0,
        )

        response = self.client.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(flow.name, response.rendered_content)

    def test_recovery_flow(self):
        """Test that recovery flow is linked correctly"""
        flow = Flow.objects.create(
            name="recovery-test",
            slug="unique-recovery-string",
            designation=FlowDesignation.RECOVERY,
        )
        FlowStageBinding.objects.create(
            flow=flow, stage=self.stage, order=0,
        )

        response = self.client.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(flow.slug, response.rendered_content)
