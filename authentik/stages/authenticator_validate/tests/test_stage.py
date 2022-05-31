"""Test validator stage"""
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from django.urls.base import reverse
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow, FlowStageBinding, NotConfiguredAction
from authentik.flows.stage import StageView
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.tests.utils import dummy_get_response
from authentik.stages.authenticator_validate.api import AuthenticatorValidateStageSerializer
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage
from authentik.stages.authenticator_validate.stage import (
    SESSION_KEY_DEVICE_CHALLENGES,
    AuthenticatorValidationChallengeResponse,
)
from authentik.stages.identification.models import IdentificationStage, UserFields


class AuthenticatorValidateStageTests(FlowTestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()

    def test_not_configured_action(self):
        """Test not_configured_action"""
        conf_stage = IdentificationStage.objects.create(
            name="conf",
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            not_configured_action=NotConfiguredAction.CONFIGURE,
        )
        stage.configuration_stages.set([conf_stage])
        flow = Flow.objects.create(name="test", slug="test", title="test")
        FlowStageBinding.objects.create(target=flow, stage=conf_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            follow=True,
        )
        self.assertStageResponse(
            response,
            flow,
            component="ak-stage-identification",
            password_fields=False,
            primary_action="Log in",
            user_fields=["username"],
            sources=[],
            show_source_labels=False,
        )

    def test_stage_validation(self):
        """Test serializer validation"""
        self.client.force_login(self.user)
        serializer = AuthenticatorValidateStageSerializer(
            data={"name": "foo", "not_configured_action": NotConfiguredAction.CONFIGURE}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("not_configured_action", serializer.errors)
        serializer = AuthenticatorValidateStageSerializer(
            data={"name": "foo", "not_configured_action": NotConfiguredAction.DENY}
        )
        self.assertTrue(serializer.is_valid())

    def test_validate_selected_challenge(self):
        """Test validate_selected_challenge"""
        # Prepare request with session
        request = self.request_factory.get("/")

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session[SESSION_KEY_DEVICE_CHALLENGES] = [
            {
                "device_class": "static",
                "device_uid": "1",
            },
            {
                "device_class": "totp",
                "device_uid": "2",
            },
        ]
        request.session.save()

        res = AuthenticatorValidationChallengeResponse()
        res.stage = StageView(FlowExecutorView())
        res.stage.request = request
        with self.assertRaises(ValidationError):
            res.validate_selected_challenge(
                {
                    "device_class": "baz",
                    "device_uid": "quox",
                }
            )
        res.validate_selected_challenge(
            {
                "device_class": "static",
                "device_uid": "1",
            }
        )
