"""identification tests"""
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.models import PasswordStage


class TestIdentificationStage(FlowTestCase):
    """Identification tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()

        # OAuthSource for the login view
        source = OAuthSource.objects.create(name="test", slug="test")

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
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
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_valid_with_password(self):
        """Test with valid email and password in single step"""
        pw_stage = PasswordStage.objects.create(name="password", backends=[BACKEND_INBUILT])
        self.stage.password_stage = pw_stage
        self.stage.save()
        form_data = {"uid_field": self.user.email, "password": self.user.username}
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_invalid_with_password(self):
        """Test with valid email and invalid password in single step"""
        pw_stage = PasswordStage.objects.create(name="password", backends=[BACKEND_INBUILT])
        self.stage.password_stage = pw_stage
        self.stage.save()
        form_data = {
            "uid_field": self.user.email,
            "password": self.user.username + "test",
        }
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-identification",
            password_fields=True,
            primary_action="Log in",
            response_errors={
                "non_field_errors": [{"code": "invalid", "string": "Failed to " "authenticate."}]
            },
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
                        "type": ChallengeTypes.REDIRECT.value,
                    },
                    "icon_url": "/static/authentik/sources/default.svg",
                    "name": "test",
                }
            ],
            show_source_labels=False,
            user_fields=["email"],
        )

    def test_invalid_with_username(self):
        """Test invalid with username (user exists but stage only allows email)"""
        form_data = {"uid_field": self.user.username}
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            form_data,
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_no_fields(self):
        """Test invalid with username (no user fields are enabled)"""
        self.stage.user_fields = []
        self.stage.save()
        form_data = {"uid_field": self.user.username}
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            form_data,
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-identification",
            password_fields=False,
            primary_action="Log in",
            response_errors={
                "non_field_errors": [{"code": "invalid", "string": "Failed to " "authenticate."}]
            },
            show_source_labels=False,
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
                        "type": ChallengeTypes.REDIRECT.value,
                    },
                    "icon_url": "/static/authentik/sources/default.svg",
                    "name": "test",
                }
            ],
            user_fields=[],
        )

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
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-identification",
            user_fields=["email"],
            password_fields=False,
            enroll_url=reverse(
                "authentik_core:if-flow",
                kwargs={"flow_slug": "unique-enrollment-string"},
            ),
            show_source_labels=False,
            primary_action="Log in",
            sources=[
                {
                    "icon_url": "/static/authentik/sources/default.svg",
                    "name": "test",
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
                        "type": ChallengeTypes.REDIRECT.value,
                    },
                }
            ],
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
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-identification",
            user_fields=["email"],
            password_fields=False,
            recovery_url=reverse(
                "authentik_core:if-flow",
                kwargs={"flow_slug": "unique-recovery-string"},
            ),
            show_source_labels=False,
            primary_action="Log in",
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
                        "type": ChallengeTypes.REDIRECT.value,
                    },
                    "icon_url": "/static/authentik/sources/default.svg",
                    "name": "test",
                }
            ],
        )
