"""Test Users API"""
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.models import Flow, FlowDesignation
from authentik.stages.email.models import EmailStage
from authentik.tenants.models import Tenant


class TestUsersAPI(APITestCase):
    """Test Users API"""

    def setUp(self) -> None:
        self.admin = User.objects.get(username="akadmin")
        self.user = User.objects.create(username="test-user")

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
