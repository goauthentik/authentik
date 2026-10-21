"""Test write-only field exposure in API responses"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.crypto.secrets.tests.utils import create_test_secret
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSProviders


class TestWriteOnlyFields(APITestCase):
    """Credentials are never rendered by their consumers, whatever the caller holds"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.group = Group.objects.create(name=generate_id())
        self.group.roles.add(self.role)
        self.group.users.add(self.user)

        AuthenticatorSMSStage.objects.all().delete()
        self.auth = create_test_secret(generate_id())
        self.auth_password = create_test_secret(generate_id())
        self.stage = AuthenticatorSMSStage.objects.create(
            name=generate_id(),
            provider=SMSProviders.GENERIC,
            from_number=generate_id(),
            auth_ref=self.auth,
            auth_password_ref=self.auth_password,
        )

    def assert_hidden(self, url: str):
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        for secret in [self.auth, self.auth_password]:
            self.assertIn(str(secret.pk), res.content.decode())
            self.assertNotIn(secret.secret_value, res.content.decode())

    def test_detail_and_list(self):
        """Values are hidden for users who can only view the stage"""
        self.role.assign_perms("authentik_stages_authenticator_sms.view_authenticatorsmsstage")
        self.client.force_login(self.user)
        self.assert_hidden(
            reverse(
                "authentik_api:authenticatorsmsstage-detail",
                kwargs={"pk": self.stage.pk},
            )
        )
        self.assert_hidden(reverse("authentik_api:authenticatorsmsstage-list"))

    def test_change_permission(self):
        """Values are hidden for users who can change the stage"""
        self.role.assign_perms(
            [
                "authentik_stages_authenticator_sms.view_authenticatorsmsstage",
                "authentik_stages_authenticator_sms.change_authenticatorsmsstage",
            ]
        )
        self.client.force_login(self.user)
        self.assert_hidden(
            reverse(
                "authentik_api:authenticatorsmsstage-detail",
                kwargs={"pk": self.stage.pk},
            )
        )

    def test_superuser(self):
        """Values are hidden for superusers"""
        self.client.force_login(create_test_admin_user())
        self.assert_hidden(
            reverse(
                "authentik_api:authenticatorsmsstage-detail",
                kwargs={"pk": self.stage.pk},
            )
        )
