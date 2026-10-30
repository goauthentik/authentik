"""proxy provider tests"""

from json import loads

from django.apps import apps
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.oauth2.models import ClientType
from authentik.providers.proxy.models import ProxyMode, ProxyProvider


class ProxyProviderTests(APITestCase):
    """proxy provider tests"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_basic_auth(self):
        """Test basic_auth_enabled"""
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": generate_id(),
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "invalidation_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
                "basic_auth_enabled": True,
                "basic_auth_user_attribute": generate_id(),
                "basic_auth_password_attribute": generate_id(),
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_basic_auth_invalid(self):
        """Test basic_auth_enabled"""
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": generate_id(),
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "invalidation_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
                "basic_auth_enabled": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "basic_auth_enabled": [
                    "User and password attributes must be set when basic auth is enabled."
                ]
            },
        )

    def test_validate(self):
        """Test validate"""
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": generate_id(),
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "invalidation_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"internal_host": ["Internal host cannot be empty when forward auth is disabled."]},
        )

    def test_create_defaults(self):
        """Test create"""
        name = generate_id()
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": name,
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "invalidation_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
            },
        )
        self.assertEqual(response.status_code, 201)
        provider: ProxyProvider = ProxyProvider.objects.get(name=name)
        self.assertEqual(provider.client_type, ClientType.CONFIDENTIAL)

    def test_update_defaults(self):
        """Test create"""
        name = generate_id()
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": name,
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "invalidation_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
            },
        )
        self.assertEqual(response.status_code, 201)
        provider: ProxyProvider = ProxyProvider.objects.get(name=name)
        self.assertEqual(provider.client_type, ClientType.CONFIDENTIAL)
        provider.client_type = ClientType.PUBLIC
        provider.save()
        response = self.client.put(
            reverse("authentik_api:proxyprovider-detail", kwargs={"pk": provider.pk}),
            {
                "name": name,
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "invalidation_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
            },
        )
        self.assertEqual(response.status_code, 200)
        provider: ProxyProvider = ProxyProvider.objects.get(name=name)
        self.assertEqual(provider.client_type, ClientType.CONFIDENTIAL)

    def test_sa_fetch(self):
        """Test fetching the outpost config as the service account"""
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.PROXY)
        provider = ProxyProvider.objects.create(name=generate_id())
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        outpost.providers.add(provider)

        res = self.client.get(
            reverse("authentik_api:proxyprovideroutpost-list"),
            HTTP_AUTHORIZATION=f"Bearer {outpost.token.key}",
        )
        body = loads(res.content)
        self.assertEqual(body["pagination"]["count"], 1)

    def test_sa_perms_cert(self):
        """Test permissions to access a configured certificate"""
        cert = create_test_cert()
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.PROXY)
        provider = ProxyProvider.objects.create(name=generate_id(), certificate=cert)
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        outpost.providers.add(provider)

        res = self.client.get(
            reverse("authentik_api:proxyprovideroutpost-list"),
            HTTP_AUTHORIZATION=f"Bearer {outpost.token.key}",
        )
        body = loads(res.content)
        self.assertEqual(body["pagination"]["count"], 1)
        cert_id = body["results"][0]["certificate"]
        self.assertEqual(cert_id, str(cert.pk))

        res = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-view-certificate",
                kwargs={
                    "pk": cert_id,
                },
            ),
            HTTP_AUTHORIZATION=f"Bearer {outpost.token.key}",
        )
        self.assertEqual(res.status_code, 200)
        # res = self.client.get(
        #     reverse(
        #         "authentik_api:certificatekeypair-view-private-key",
        #         kwargs={
        #             "pk": cert_id,
        #         },
        #     ),
        #     HTTP_AUTHORIZATION=f"Bearer {outpost.token.key}",
        # )
        # self.assertEqual(res.status_code, 200)


class ProxySetDefaultsTests(TestCase):
    """proxy_set_defaults reconciler tests"""

    def test_proxy_set_defaults_skips_unchanged_providers(self):
        """Steady-state reconciliation must not save every provider on startup."""
        provider = ProxyProvider.objects.create(
            name=generate_id(),
            mode=ProxyMode.PROXY,
            authorization_flow=create_test_flow(),
            invalidation_flow=create_test_flow(),
            external_host="http://localhost",
            internal_host="http://localhost",
        )
        provider.set_oauth_defaults()
        provider.save()

        saves: list[int] = []

        def on_save(instance, **_kwargs):
            saves.append(instance.pk)

        post_save.connect(on_save, sender=ProxyProvider, weak=False)
        try:
            apps.get_app_config("authentik_providers_proxy").proxy_set_defaults()
        finally:
            post_save.disconnect(on_save, sender=ProxyProvider)

        self.assertEqual(saves, [])

    def test_proxy_set_defaults_corrects_drift(self):
        provider = ProxyProvider.objects.create(
            name=generate_id(),
            mode=ProxyMode.PROXY,
            authorization_flow=create_test_flow(),
            invalidation_flow=create_test_flow(),
            external_host="http://localhost",
            internal_host="http://localhost",
        )
        provider.set_oauth_defaults()
        provider.save()
        provider.client_type = ClientType.PUBLIC
        provider.save(update_fields=["client_type"])

        apps.get_app_config("authentik_providers_proxy").proxy_set_defaults()

        provider.refresh_from_db()
        self.assertEqual(provider.client_type, ClientType.CONFIDENTIAL)
