"""Enterprise password stage API tests."""

from unittest.mock import PropertyMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.enterprise.stages.password.models import UserPasswordLoginState
from authentik.enterprise.tests import enterprise_test
from authentik.lib.generators import generate_id
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.api import PasswordStageSerializer
from authentik.stages.password.models import PasswordStage


class TestPasswordStageEnterpriseAPI(APITestCase):
    """Test password lockout licensing at API boundaries."""

    @patch(
        "authentik.enterprise.models.LicenseUsageStatus.is_valid",
        PropertyMock(return_value=False),
    )
    def test_lockout_configuration_requires_license(self) -> None:
        """Reject password lockout settings without an Enterprise license."""
        stage = PasswordStage.objects.create(name=generate_id(), backends=[BACKEND_INBUILT])
        serializer = PasswordStageSerializer(
            stage,
            data={"failed_attempts_before_lockout": 2},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    @enterprise_test()
    def test_lockout_configuration_with_license(self) -> None:
        """Allow password lockout settings with an Enterprise license."""
        stage = PasswordStage.objects.create(name=generate_id(), backends=[BACKEND_INBUILT])
        serializer = PasswordStageSerializer(
            stage,
            data={"failed_attempts_before_lockout": 2},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    @patch(
        "authentik.enterprise.models.LicenseUsageStatus.is_valid",
        PropertyMock(return_value=False),
    )
    def test_password_login_action_requires_license(self) -> None:
        """Reject administrative password login locks without an Enterprise license."""
        admin = create_test_admin_user()
        user = create_test_user()
        self.client.force_login(admin)

        response = self.client.post(
            reverse("authentik_api:user-password-login-lock", kwargs={"pk": user.pk})
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserPasswordLoginState.objects.filter(user=user).exists())
