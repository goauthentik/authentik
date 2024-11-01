"""identification tests"""

from django.urls import reverse
from requests_mock import Mocker
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.captcha.models import CaptchaStage
from authentik.stages.captcha.tests import RECAPTCHA_PRIVATE_KEY, RECAPTCHA_PUBLIC_KEY
from authentik.stages.identification.api import IdentificationStageSerializer
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
            pretend_user_exists=False,
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
                "non_field_errors": [{"code": "invalid", "string": "Failed to authenticate."}]
            },
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
                    },
                    "icon_url": "/static/authentik/sources/default.svg",
                    "name": "test",
                }
            ],
            show_source_labels=False,
            user_fields=["email"],
        )

    def test_invalid_with_password_pretend(self):
        """Test with invalid email and invalid password in single step (with pretend_user_exists)"""
        self.stage.pretend_user_exists = True
        pw_stage = PasswordStage.objects.create(name="password", backends=[BACKEND_INBUILT])
        self.stage.password_stage = pw_stage
        self.stage.save()
        form_data = {
            "uid_field": self.user.email + "test",
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
                "non_field_errors": [{"code": "invalid", "string": "Failed to authenticate."}]
            },
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
                    },
                    "icon_url": "/static/authentik/sources/default.svg",
                    "name": "test",
                }
            ],
            show_source_labels=False,
            user_fields=["email"],
        )

    @Mocker()
    def test_valid_with_captcha(self, mock: Mocker):
        """Test with valid email and captcha token in single step"""
        mock.post(
            "https://www.recaptcha.net/recaptcha/api/siteverify",
            json={
                "success": True,
                "score": 0.5,
            },
        )

        captcha_stage = CaptchaStage.objects.create(
            name="captcha",
            public_key=RECAPTCHA_PUBLIC_KEY,
            private_key=RECAPTCHA_PRIVATE_KEY,
        )
        self.stage.captcha_stage = captcha_stage
        self.stage.save()

        form_data = {"uid_field": self.user.email, "captcha_token": "PASSED"}
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    @Mocker()
    def test_invalid_with_captcha(self, mock: Mocker):
        """Test with valid email and invalid captcha token in single step"""
        mock.post(
            "https://www.recaptcha.net/recaptcha/api/siteverify",
            json={
                "success": False,
                "score": 0.5,
            },
        )

        captcha_stage = CaptchaStage.objects.create(
            name="captcha",
            public_key=RECAPTCHA_PUBLIC_KEY,
            private_key=RECAPTCHA_PRIVATE_KEY,
        )

        self.stage.captcha_stage = captcha_stage
        self.stage.save()

        form_data = {
            "uid_field": self.user.email,
            "captcha_token": "FAILED",
        }
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-identification",
            password_fields=False,
            primary_action="Log in",
            response_errors={
                "non_field_errors": [{"code": "invalid", "string": "Invalid captcha response"}]
            },
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
                    },
                    "icon_url": "/static/authentik/sources/default.svg",
                    "name": "test",
                }
            ],
            show_source_labels=False,
            user_fields=["email"],
        )

    @Mocker()
    def test_invalid_with_captcha_retriable(self, mock: Mocker):
        """Test with valid email and invalid captcha token in single step"""
        mock.post(
            "https://www.recaptcha.net/recaptcha/api/siteverify",
            json={
                "success": False,
                "score": 0.5,
                "error-codes": ["timeout-or-duplicate"],
            },
        )

        captcha_stage = CaptchaStage.objects.create(
            name="captcha",
            public_key=RECAPTCHA_PUBLIC_KEY,
            private_key=RECAPTCHA_PRIVATE_KEY,
        )

        self.stage.captcha_stage = captcha_stage
        self.stage.save()

        form_data = {
            "uid_field": self.user.email,
            "captcha_token": "FAILED",
        }
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-identification",
            password_fields=False,
            primary_action="Log in",
            response_errors={
                "non_field_errors": [
                    {
                        "code": "invalid",
                        "string": "Invalid captcha response. Retrying may solve this issue.",
                    }
                ]
            },
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
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
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-identification",
            response_errors={
                "non_field_errors": [{"string": "Failed to authenticate.", "code": "invalid"}]
            },
        )

    def test_invalid_with_username_pretend(self):
        """Test invalid with username (user exists but stage only allows email)"""
        self.stage.pretend_user_exists = True
        self.stage.save()
        form_data = {"uid_field": self.user.username}
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            form_data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

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
                "non_field_errors": [{"code": "invalid", "string": "Failed to authenticate."}]
            },
            show_source_labels=False,
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
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
        flow = create_test_flow()
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
                kwargs={"flow_slug": flow.slug},
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
                    },
                }
            ],
        )

    def test_link_recovery_flow(self):
        """Test that recovery flow is linked correctly"""
        flow = create_test_flow()
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
                kwargs={"flow_slug": flow.slug},
            ),
            show_source_labels=False,
            primary_action="Log in",
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
                    },
                    "icon_url": "/static/authentik/sources/default.svg",
                    "name": "test",
                }
            ],
        )

    def test_recovery_flow_invalid_user(self):
        """Test that an invalid user can proceed in a recovery flow"""
        self.flow.designation = FlowDesignation.RECOVERY
        self.flow.save()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-identification",
            user_fields=["email"],
            password_fields=False,
            show_source_labels=False,
            primary_action="Continue",
            sources=[
                {
                    "challenge": {
                        "component": "xak-flow-redirect",
                        "to": "/source/oauth/login/test/",
                    },
                    "icon_url": "/static/authentik/sources/default.svg",
                    "name": "test",
                }
            ],
        )
        form_data = {"uid_field": generate_id()}
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 200)

    def test_api_validate(self):
        """Test API validation"""
        self.assertTrue(
            IdentificationStageSerializer(
                data={
                    "name": generate_id(),
                    "user_fields": [UserFields.E_MAIL, UserFields.USERNAME],
                }
            ).is_valid(raise_exception=True)
        )
        with self.assertRaises(ValidationError):
            IdentificationStageSerializer(
                data={
                    "name": generate_id(),
                    "user_fields": [],
                    "sources": [],
                }
            ).is_valid(raise_exception=True)
