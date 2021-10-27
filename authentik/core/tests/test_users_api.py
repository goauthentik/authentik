"""Test Users API"""
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import USER_ATTRIBUTE_CHANGE_EMAIL, USER_ATTRIBUTE_CHANGE_USERNAME, User
from authentik.flows.models import Flow, FlowDesignation
from authentik.stages.email.models import EmailStage
from authentik.tenants.models import Tenant


class TestUsersAPI(APITestCase):
    """Test Users API"""

    def setUp(self) -> None:
        self.admin = User.objects.get(username="akadmin")
        self.user = User.objects.create(username="test-user")

    def test_update_self(self):
        """Test update_self"""
        self.client.force_login(self.admin)
        response = self.client.put(
            reverse("authentik_api:user-update-self"), data={"username": "foo", "name": "foo"}
        )
        self.assertEqual(response.status_code, 200)

    def test_update_self_username_denied(self):
        """Test update_self"""
        self.admin.attributes[USER_ATTRIBUTE_CHANGE_USERNAME] = False
        self.admin.save()
        self.client.force_login(self.admin)
        response = self.client.put(
            reverse("authentik_api:user-update-self"), data={"username": "foo", "name": "foo"}
        )
        self.assertEqual(response.status_code, 400)

    def test_update_self_email_denied(self):
        """Test update_self"""
        self.admin.attributes[USER_ATTRIBUTE_CHANGE_EMAIL] = False
        self.admin.save()
        self.client.force_login(self.admin)
        response = self.client.put(
            reverse("authentik_api:user-update-self"), data={"email": "foo", "name": "foo"}
        )
        self.assertEqual(response.status_code, 400)

    def test_metrics(self):
        """Test user's metrics"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-metrics", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_metrics_denied(self):
        """Test user's metrics (non-superuser)"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("authentik_api:user-metrics", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_recovery_no_flow(self):
        """Test user recovery link (no recovery flow set)"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-recovery", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_recovery(self):
        """Test user recovery link (no recovery flow set)"""
        flow = Flow.objects.create(
            name="test", title="test", slug="test", designation=FlowDesignation.RECOVERY
        )
        tenant: Tenant = Tenant.objects.first()
        tenant.flow_recovery = flow
        tenant.save()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-recovery", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_recovery_email_no_flow(self):
        """Test user recovery link (no recovery flow set)"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-recovery-email", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.user.email = "foo@bar.baz"
        self.user.save()
        response = self.client.get(
            reverse("authentik_api:user-recovery-email", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_recovery_email_no_stage(self):
        """Test user recovery link (no email stage)"""
        self.user.email = "foo@bar.baz"
        self.user.save()
        flow = Flow.objects.create(
            name="test", title="test", slug="test", designation=FlowDesignation.RECOVERY
        )
        tenant: Tenant = Tenant.objects.first()
        tenant.flow_recovery = flow
        tenant.save()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-recovery-email", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_recovery_email(self):
        """Test user recovery link"""
        self.user.email = "foo@bar.baz"
        self.user.save()
        flow = Flow.objects.create(
            name="test", title="test", slug="test", designation=FlowDesignation.RECOVERY
        )
        tenant: Tenant = Tenant.objects.first()
        tenant.flow_recovery = flow
        tenant.save()

        stage = EmailStage.objects.create(name="email")

        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "authentik_api:user-recovery-email",
                kwargs={"pk": self.user.pk},
            )
            + f"?email_stage={stage.pk}"
        )
        self.assertEqual(response.status_code, 204)

    def test_service_account(self):
        """Service account creation"""
        self.client.force_login(self.admin)
        response = self.client.post(reverse("authentik_api:user-service-account"))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="test-sa").exists())

    def test_service_account_invalid(self):
        """Service account creation (twice with same name, expect error)"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="test-sa").exists())
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 400)
