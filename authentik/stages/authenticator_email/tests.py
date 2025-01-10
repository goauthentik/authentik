"""Test Email API"""

from unittest.mock import MagicMock, patch

from django.urls import reverse
from structlog.stdlib import get_logger

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage, EmailDevice

LOGGER = get_logger()


class TestAuthenticatorEmailStage(FlowTestCase):
    """Test Email Authenticator stage"""

    def setUp(self):
        super().setUp()
        self.flow = create_test_flow()
        self.user = create_test_admin_user()
        self.stage = AuthenticatorEmailStage.objects.create(
            name="email-authenticator",
            use_global_settings=True,
            from_address="test@authentik.local",
            configure_flow=self.flow,
        )
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)
        self.device = EmailDevice.objects.create(
            user=self.user,
            stage=self.stage,
            email="test@authentik.local",
        )
        self.client.force_login(self.user)

    def test_stage_no_prefill(self):
        self.client.get(
            reverse("authentik_flows:configure", kwargs={"stage_uuid": self.stage.stage_uuid}),
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-email",
        )

    def test_token(self):
        # Make sure that the token doesn't exist
        assert self.device.token is None
        # Create the token
        self.device.generate_token()
        # Make sure that the token was generated
        assert self.device.token is not None
        # Make sure that the token can be verified and is invalid
        assert self.device.verify_token("invalid_token") is False
        # Verify the token
        assert self.device.verify_token(self.device.token)
        # Make sure that the token was cleared
        assert self.device.token is None

    def test_stage_send(self):
        # Initialize the flow
        self.client.get(
            reverse("authentik_flows:configure", kwargs={"stage_uuid": self.stage.stage_uuid}),
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-email",
        )

        # Test email submission
        email_send_mock = MagicMock()
        with patch(
            "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.send",
            email_send_mock,
        ):
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                data={"component": "ak-stage-authenticator-email", "email": "test@example.com"},
            )
            self.assertEqual(response.status_code, 200)
            email_send_mock.assert_called_once()

        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-email",
            response_errors={},
            email_required=False,
        )

        # Test email submission with no email
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"component": "ak-stage-authenticator-email"},
        )
        self.assertEqual(response.status_code, 200)  # Test invalid email
        LOGGER.warn(response.content.decode())
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-email",
            response_errors={"non_field_errors": [{"string": "email required", "code": "invalid"}]},
            # email_required=False,
        )
