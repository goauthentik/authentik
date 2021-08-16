"""identification tests"""
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.providers.oauth2.generators import generate_client_secret
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password import BACKEND_DJANGO
from authentik.stages.password.models import PasswordStage


class TestIdentificationStage(TestCase):
    """Identification tests"""

    def setUp(self):
        super().setUp()
        self.password = generate_client_secret()
        self.user = User.objects.create_user(
            username="unittest", email="test@beryju.org", password=self.password
        )
        self.client = Client()

        # OAuthSource for the login view
        source = OAuthSource.objects.create(name="test", slug="test")

        self.flow = Flow.objects.create(
            name="test-identification",
            slug="test-identification",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = IdentificationStage.objects.create(
            name="identification",
            user_fields=[UserFields.E_MAIL],
        )
        self.stage.sources.set([source])
        self.stage.save()
        FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )

    def test_valid_render(self):
        """Test that View renders correctly"""
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_valid_with_email(self):
        """Test with valid email, check that URL redirects back to itself"""
        form_data = {"uid_field": self.user.email}
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )

    def test_valid_with_password(self):
        """Test with valid email and password in single step"""
        pw_stage = PasswordStage.objects.create(name="password", backends=[BACKEND_DJANGO])
        self.stage.password_stage = pw_stage
        self.stage.save()
        form_data = {"uid_field": self.user.email, "password": self.password}
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )

    def test_invalid_with_password(self):
        """Test with valid email and invalid password in single step"""
        pw_stage = PasswordStage.objects.create(name="password", backends=[BACKEND_DJANGO])
        self.stage.password_stage = pw_stage
        self.stage.save()
        form_data = {
            "uid_field": self.user.email,
            "password": self.password + "test",
        }
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "type": ChallengeTypes.NATIVE.value,
                "component": "ak-stage-identification",
                "password_fields": True,
                "primary_action": "Log in",
                "response_errors": {
                    "non_field_errors": [
                        {"code": "invalid", "string": "Failed to " "authenticate."}
                    ]
                },
                "flow_info": {
                    "background": self.flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": "",
                },
                "sources": [
                    {
                        "challenge": {
                            "component": "xak-flow-redirect",
                            "to": "/source/oauth/login/test/",
                            "type": ChallengeTypes.REDIRECT.value,
                        },
                        "icon_url": "/static/authentik/sources/.svg",
                        "name": "test",
                    }
                ],
                "user_fields": ["email"],
            },
        )

    def test_invalid_with_username(self):
        """Test invalid with username (user exists but stage only allows email)"""
        form_data = {"uid_field": self.user.username}
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            form_data,
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_with_invalid_email(self):
        """Test with invalid email (user doesn't exist) -> Will return to login form"""
        form_data = {"uid_field": self.user.email + "test"}
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
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
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "type": ChallengeTypes.NATIVE.value,
                "component": "ak-stage-identification",
                "user_fields": ["email"],
                "password_fields": False,
                "enroll_url": reverse(
                    "authentik_core:if-flow",
                    kwargs={"flow_slug": "unique-enrollment-string"},
                ),
                "primary_action": "Log in",
                "flow_info": {
                    "background": flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": self.flow.title,
                },
                "sources": [
                    {
                        "icon_url": "/static/authentik/sources/.svg",
                        "name": "test",
                        "challenge": {
                            "component": "xak-flow-redirect",
                            "to": "/source/oauth/login/test/",
                            "type": ChallengeTypes.REDIRECT.value,
                        },
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
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "type": ChallengeTypes.NATIVE.value,
                "component": "ak-stage-identification",
                "user_fields": ["email"],
                "password_fields": False,
                "recovery_url": reverse(
                    "authentik_core:if-flow",
                    kwargs={"flow_slug": "unique-recovery-string"},
                ),
                "primary_action": "Log in",
                "flow_info": {
                    "background": flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": self.flow.title,
                },
                "sources": [
                    {
                        "challenge": {
                            "component": "xak-flow-redirect",
                            "to": "/source/oauth/login/test/",
                            "type": ChallengeTypes.REDIRECT.value,
                        },
                        "icon_url": "/static/authentik/sources/.svg",
                        "name": "test",
                    }
                ],
            },
        )
