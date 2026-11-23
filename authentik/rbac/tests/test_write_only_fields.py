"""Test write-only field exposure in API responses"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSProviders


class TestWriteOnlyFields(APITestCase):
    """Test that write-only fields are never rendered, whatever the caller holds"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.group = Group.objects.create(name=generate_id())
        self.group.roles.add(self.role)
        self.group.users.add(self.user)

        AuthenticatorSMSStage.objects.all().delete()
        self.auth = generate_id()
        self.auth_password = generate_id()
        self.stage = AuthenticatorSMSStage.objects.create(
            name=generate_id(),
            provider=SMSProviders.GENERIC,
            from_number=generate_id(),
            account_sid=generate_id(),
            auth=self.auth,
            auth_password=self.auth_password,
        )

    def test_stage_detail_view(self):
        """Test stage detail (role has global view permission)"""
        self.role.assign_perms("authentik_stages_authenticator_sms.view_authenticatorsmsstage")
        self.client.force_login(self.user)

        res = self.client.get(
            reverse("authentik_api:authenticatorsmsstage-detail", kwargs={"pk": self.stage.pk})
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertNotIn("auth", body)
        self.assertNotIn("auth_password", body)
        self.assertEqual(body["account_sid"], self.stage.account_sid)

    def test_stage_list_view(self):
        """Test stage list (role has global view permission)"""
        self.role.assign_perms("authentik_stages_authenticator_sms.view_authenticatorsmsstage")
        self.client.force_login(self.user)

        res = self.client.get(reverse("authentik_api:authenticatorsmsstage-list"))
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["pagination"]["count"], 1)
        self.assertNotIn("auth", body["results"][0])
        self.assertNotIn("auth_password", body["results"][0])
        self.assertEqual(body["results"][0]["account_sid"], self.stage.account_sid)

    def test_stage_detail_change_global(self):
        """Test stage detail (role has global change permission)"""
        self.role.assign_perms(
            [
                "authentik_stages_authenticator_sms.view_authenticatorsmsstage",
                "authentik_stages_authenticator_sms.change_authenticatorsmsstage",
            ]
        )
        self.client.force_login(self.user)

        res = self.client.get(
            reverse("authentik_api:authenticatorsmsstage-detail", kwargs={"pk": self.stage.pk})
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertNotIn("auth", body)
        self.assertNotIn("auth_password", body)

    def test_stage_detail_superuser(self):
        """Test stage detail (superuser)"""
        self.client.force_login(create_test_admin_user())

        res = self.client.get(
            reverse("authentik_api:authenticatorsmsstage-detail", kwargs={"pk": self.stage.pk})
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertNotIn("auth", body)
        self.assertNotIn("auth_password", body)

    def test_stage_create(self):
        """Test stage create (the response omits the values that were stored)"""
        self.role.assign_perms("authentik_stages_authenticator_sms.add_authenticatorsmsstage")
        self.client.force_login(self.user)

        name = generate_id()
        auth = generate_id()
        auth_password = generate_id()
        res = self.client.post(
            reverse("authentik_api:authenticatorsmsstage-list"),
            {
                "name": name,
                "provider": SMSProviders.GENERIC,
                "from_number": generate_id(),
                "account_sid": generate_id(),
                "auth": auth,
                "auth_password": auth_password,
            },
        )
        self.assertEqual(res.status_code, 201)
        body = loads(res.content)
        self.assertNotIn("auth", body)
        self.assertNotIn("auth_password", body)
        stage = AuthenticatorSMSStage.objects.get(name=name)
        self.assertEqual(stage.auth, auth)
        self.assertEqual(stage.auth_password, auth_password)

    def test_stage_partial_update_keeps_values(self):
        """Test stage partial update without the write-only fields (as the admin UI sends it)"""
        self.client.force_login(create_test_admin_user())

        from_number = generate_id()
        res = self.client.patch(
            reverse("authentik_api:authenticatorsmsstage-detail", kwargs={"pk": self.stage.pk}),
            {"from_number": from_number},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.stage.refresh_from_db()
        self.assertEqual(self.stage.from_number, from_number)
        self.assertEqual(self.stage.auth, self.auth)
        self.assertEqual(self.stage.auth_password, self.auth_password)
