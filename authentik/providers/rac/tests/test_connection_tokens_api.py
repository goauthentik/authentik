"""Test Connection Tokens API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import ConnectionToken, Protocols, RACProvider
from authentik.providers.rac.tests import create_test_device


class TestConnectionTokensAPI(APITestCase):
    """Test connection tokens API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()
        self.provider_secret = generate_id()
        self.provider = RACProvider.objects.create(
            name=generate_id(),
            settings={"password": self.provider_secret},
        )
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.device = create_test_device(host=f"{generate_id()}:3389")
        session = Session.objects.create(session_key=generate_id(), last_ip="255.255.255.255")
        auth_session = AuthenticatedSession.objects.create(session=session, user=self.user)
        self.token = ConnectionToken.objects.create(
            provider=self.provider,
            device=self.device,
            protocol=Protocols.RDP,
            session=auth_session,
        )

    def test_owner_does_not_see_settings(self):
        """The token owner can list and retrieve their own token but must not receive the
        connection settings, which can hold credentials. The connection itself is built
        server-side from the token, not from this endpoint."""
        self.assertFalse(self.user.has_perm("authentik_providers_rac.view_racprovider"))
        self.client.force_login(self.user)

        response = self.client.get(reverse("authentik_api:connectiontoken-list"))
        self.assertEqual(response.status_code, 200)
        result = next(r for r in response.json()["results"] if r["pk"] == str(self.token.pk))
        self.assertEqual(result["device_name"], self.device.name)
        self.assertEqual(result["provider_obj"]["settings"], {})
        self.assertNotIn(self.provider_secret, response.content.decode())

        response = self.client.get(
            reverse("authentik_api:connectiontoken-detail", kwargs={"pk": str(self.token.pk)})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider_obj"]["settings"], {})
        self.assertNotIn(self.provider_secret, response.content.decode())

    def test_manager_sees_provider_settings(self):
        """A user who can manage the provider still receives its settings"""
        self.client.force_login(self.admin)

        response = self.client.get(reverse("authentik_api:connectiontoken-list"))
        self.assertEqual(response.status_code, 200)
        result = next(r for r in response.json()["results"] if r["pk"] == str(self.token.pk))
        self.assertEqual(result["provider_obj"]["settings"], {"password": self.provider_secret})

        response = self.client.get(
            reverse("authentik_api:connectiontoken-detail", kwargs={"pk": str(self.token.pk)})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["provider_obj"]["settings"], {"password": self.provider_secret}
        )
