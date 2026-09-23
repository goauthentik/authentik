"""Test Connection Tokens API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import ConnectionToken, Endpoint, Protocols, RACProvider


class TestConnectionTokensAPI(APITestCase):
    """Test connection tokens API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()
        self.endpoint_secret = generate_id()
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
        self.endpoint = Endpoint.objects.create(
            name=generate_id(),
            host=f"{generate_id()}:3389",
            protocol=Protocols.RDP,
            auth_mode="static",
            settings={"username": "user", "password": self.endpoint_secret},
            provider=self.provider,
        )
        session = Session.objects.create(session_key=generate_id(), last_ip="255.255.255.255")
        auth_session = AuthenticatedSession.objects.create(session=session, user=self.user)
        self.token = ConnectionToken.objects.create(
            provider=self.provider,
            endpoint=self.endpoint,
            session=auth_session,
        )

    def test_owner_does_not_see_nested_settings(self):
        """The token owner can list and retrieve their own token but must not receive the
        nested endpoint/provider settings, which can hold connection credentials. The
        connection itself is built server-side from the token, not from this field."""
        self.assertFalse(self.user.has_perm("authentik_providers_rac.view_endpoint"))
        self.client.force_login(self.user)

        response = self.client.get(reverse("authentik_api:connectiontoken-list"))
        self.assertEqual(response.status_code, 200)
        result = next(r for r in response.json()["results"] if r["pk"] == str(self.token.pk))
        self.assertEqual(result["endpoint_obj"]["settings"], {})
        self.assertEqual(result["provider_obj"]["settings"], {})
        self.assertNotIn(self.endpoint_secret, response.content.decode())
        self.assertNotIn(self.provider_secret, response.content.decode())

        response = self.client.get(
            reverse("authentik_api:connectiontoken-detail", kwargs={"pk": str(self.token.pk)})
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["endpoint_obj"]["settings"], {})
        self.assertEqual(result["provider_obj"]["settings"], {})
        self.assertNotIn(self.endpoint_secret, response.content.decode())
        self.assertNotIn(self.provider_secret, response.content.decode())

    def test_manager_sees_nested_settings(self):
        """A user who can manage the endpoint/provider still receives the settings, from
        both the list and the detail endpoint."""
        self.client.force_login(self.admin)

        response = self.client.get(reverse("authentik_api:connectiontoken-list"))
        self.assertEqual(response.status_code, 200)
        result = next(r for r in response.json()["results"] if r["pk"] == str(self.token.pk))
        self.assertEqual(
            result["endpoint_obj"]["settings"],
            {"username": "user", "password": self.endpoint_secret},
        )
        self.assertEqual(result["provider_obj"]["settings"], {"password": self.provider_secret})

        response = self.client.get(
            reverse("authentik_api:connectiontoken-detail", kwargs={"pk": str(self.token.pk)})
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(
            result["endpoint_obj"]["settings"],
            {"username": "user", "password": self.endpoint_secret},
        )
        self.assertEqual(result["provider_obj"]["settings"], {"password": self.provider_secret})
