"""identification tests"""
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.identification.models import IdentificationStage, UserFields


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
        )
        FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )

        # OAuthSource for the login view
        OAuthSource.objects.create(name="test", slug="test")

    def test_valid_render(self):
        """Test that View renders correctly"""
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_valid_with_email(self):
        """Test with valid email, check that URL redirects back to itself"""
        form_data = {"uid_field": self.user.email}
        url = reverse(
            "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
        )
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"to": reverse("authentik_core:if-admin"), "type": "redirect"},
        )

    def test_invalid_with_username(self):
        """Test invalid with username (user exists but stage only allows email)"""
        form_data = {"uid_field": self.user.username}
        response = self.client.post(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            form_data,
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_with_invalid_email(self):
        """Test with invalid email (user doesn't exist) -> Will return to login form"""
        form_data = {"uid_field": self.user.email + "test"}
        response = self.client.post(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            form_data,
        )
        self.assertEqual(response.status_code, 200)

    def test_enrollment_flow(self):
        """Test that enrollment flow is linked correctly"""
        flow = Flow.objects.create(
            name="enroll-test",
            slug="unique-enrollment-string",
            title="unique-enrollment-string",
            designation=FlowDesignation.ENROLLMENT,
        )
        self.stage.enrollment_flow = flow
        self.stage.save()
        FlowStageBinding.objects.create(
            target=flow,
            stage=self.stage,
            order=0,
        )

        response = self.client.get(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "type": ChallengeTypes.native.value,
                "component": "ak-stage-identification",
                "input_type": "email",
                "enroll_url": "/flows/unique-enrollment-string/",
                "primary_action": "Log in",
                "title": self.flow.title,
                "sources": [
                    {
                        "icon_url": "/static/authentik/sources/.svg",
                        "name": "test",
                        "url": "/source/oauth/login/test/",
                    }
                ],
            },
        )

    def test_recovery_flow(self):
        """Test that recovery flow is linked correctly"""
        flow = Flow.objects.create(
            name="recovery-test",
            slug="unique-recovery-string",
            designation=FlowDesignation.RECOVERY,
        )
        self.stage.recovery_flow = flow
        self.stage.save()
        FlowStageBinding.objects.create(
            target=flow,
            stage=self.stage,
            order=0,
        )
        response = self.client.get(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "type": ChallengeTypes.native.value,
                "component": "ak-stage-identification",
                "input_type": "email",
                "recovery_url": "/flows/unique-recovery-string/",
                "primary_action": "Log in",
                "title": self.flow.title,
                "sources": [
                    {
                        "icon_url": "/static/authentik/sources/.svg",
                        "name": "test",
                        "url": "/source/oauth/login/test/",
                    }
                ],
            },
        )
