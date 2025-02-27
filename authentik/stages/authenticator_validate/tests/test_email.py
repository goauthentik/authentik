"""Test validator stage for Email devices"""

from django.test.client import RequestFactory
from django.urls.base import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowStageBinding, NotConfiguredAction
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.lib.utils.email import mask_email
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage, EmailDevice
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.identification.models import IdentificationStage, UserFields


class AuthenticatorValidateStageEmailTests(FlowTestCase):
    """Test validator stage for Email devices"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()
        # Create email authenticator stage
        self.stage = AuthenticatorEmailStage.objects.create(
            name="email-authenticator",
            use_global_settings=True,
            from_address="test@authentik.local",
        )
        # Create identification stage
        self.ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[UserFields.USERNAME],
        )
        # Create validation stage
        self.validate_stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            device_classes=[DeviceClasses.EMAIL],
        )
        # Create flow with both stages
        self.flow = create_test_flow()
        FlowStageBinding.objects.create(target=self.flow, stage=self.ident_stage, order=0)
        FlowStageBinding.objects.create(target=self.flow, stage=self.validate_stage, order=1)

    def _identify_user(self):
        """Helper to identify user in flow"""
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"uid_field": self.user.username},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        return response

    def _send_challenge(self, device):
        """Helper to send challenge for device"""
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {
                "component": "ak-stage-authenticator-validate",
                "selected_challenge": {
                    "device_class": "email",
                    "device_uid": str(device.pk),
                    "challenge": {},
                    "last_used": device.last_used.isoformat() if device.last_used else None,
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        return response

    def test_happy_path(self):
        """Test validator stage with valid code"""
        # Create a device for our user
        device = EmailDevice.objects.create(
            user=self.user,
            confirmed=True,
            stage=self.stage,
            email="xx@0.co",
        )  # Short email for testing purposes

        # First identify the user
        self._identify_user()

        # Send the challenge
        response = self._send_challenge(device)
        response_data = self.assertStageResponse(
            response,
            flow=self.flow,
            component="ak-stage-authenticator-validate",
        )

        # Get the device challenge from the response and verify it matches
        device_challenge = response_data["device_challenges"][0]
        self.assertEqual(device_challenge["device_class"], "email")
        self.assertEqual(device_challenge["device_uid"], str(device.pk))
        self.assertEqual(device_challenge["challenge"], {"email": mask_email(device.email)})

        # Generate a token for the device
        device.generate_token()

        # Submit the valid code
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"component": "ak-stage-authenticator-validate", "code": device.token},
        )
        # Should redirect to root since this is the last stage
        self.assertStageRedirects(response, "/")

    def test_no_device(self):
        """Test validator stage without configured device"""
        configuration_stage = AuthenticatorEmailStage.objects.create(
            name=generate_id(),
            use_global_settings=True,
            from_address="test@authentik.local",
        )
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.EMAIL],
        )
        stage.configuration_stages.set([configuration_stage])
        flow = create_test_flow()
        FlowStageBinding.objects.create(target=flow, stage=stage, order=2)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"component": "ak-stage-authenticator-validate"},
        )
        self.assertEqual(response.status_code, 200)
        response_data = self.assertStageResponse(
            response,
            flow=flow,
            component="ak-stage-authenticator-validate",
        )
        self.assertEqual(response_data["configuration_stages"], [])
        self.assertEqual(response_data["device_challenges"], [])
        self.assertEqual(
            response_data["response_errors"],
            {"non_field_errors": [{"code": "invalid", "string": "Empty response"}]},
        )

    def test_invalid_code(self):
        """Test validator stage with invalid code"""
        # Create a device for our user
        device = EmailDevice.objects.create(
            user=self.user,
            confirmed=True,
            stage=self.stage,
            email="test@authentik.local",
        )

        # First identify the user
        self._identify_user()

        # Send the challenge
        self._send_challenge(device)

        # Generate a token for the device
        device.generate_token()

        # Try invalid code and verify error message
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"component": "ak-stage-authenticator-validate", "code": "invalid"},
        )
        response_data = self.assertStageResponse(
            response,
            flow=self.flow,
            component="ak-stage-authenticator-validate",
        )
        self.assertEqual(
            response_data["response_errors"],
            {
                "code": [
                    {
                        "code": "invalid",
                        "string": (
                            "Invalid Token. Please ensure the time on your device "
                            "is accurate and try again."
                        ),
                    }
                ],
            },
        )
