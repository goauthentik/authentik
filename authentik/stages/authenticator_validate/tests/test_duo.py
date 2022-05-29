"""Test validator stage"""
from unittest.mock import MagicMock, patch

from django.test.client import RequestFactory
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id, generate_key
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.challenge import validate_challenge_duo


class AuthenticatorValidateStageDuoTests(FlowTestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()

    def test_device_challenge_duo(self):
        """Test duo"""
        request = self.request_factory.get("/")
        stage = AuthenticatorDuoStage.objects.create(
            name="test",
            client_id=generate_id(),
            client_secret=generate_key(),
            api_hostname="",
        )
        duo_device = DuoDevice.objects.create(
            user=self.user,
            stage=stage,
        )
        duo_mock = MagicMock(
            auth=MagicMock(
                return_value={
                    "result": "allow",
                    "status": "allow",
                    "status_msg": "Success. Logging you in...",
                }
            )
        )
        failed_duo_mock = MagicMock(auth=MagicMock(return_value={"result": "deny"}))
        with patch(
            "authentik.stages.authenticator_duo.models.AuthenticatorDuoStage.client",
            duo_mock,
        ):
            self.assertEqual(duo_device, validate_challenge_duo(duo_device.pk, request, self.user))
        with patch(
            "authentik.stages.authenticator_duo.models.AuthenticatorDuoStage.client",
            failed_duo_mock,
        ):
            with self.assertRaises(ValidationError):
                validate_challenge_duo(duo_device.pk, request, self.user)
