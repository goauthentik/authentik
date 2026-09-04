"""Test RADIUS provider secret handling"""

from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.proxy.models import ProxyProvider
from authentik.providers.radius.models import RadiusProvider
from authentik.secrets.models import Secret


class TestProviderSecret(APITestCase):
    """Test RADIUS provider secret handling"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_auto_create(self):
        """Creating a provider without a secret creates one with a generated value"""
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        self.assertIsNotNone(provider.secret)
        self.assertNotEqual(provider.secret.value, "")

    def test_rotation_triggers_outpost_update(self):
        """Rotating a secret pushes new config to outposts whose providers use it"""
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.RADIUS)
        outpost.providers.add(provider)
        other_provider = RadiusProvider.objects.create(name=generate_id(), secret=provider.secret)
        outpost.providers.add(other_provider)
        proxy_provider = ProxyProvider.objects.create(
            name=generate_id(), secret=provider.secret, external_host="https://app.example.com"
        )
        proxy_outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.PROXY)
        proxy_outpost.providers.add(proxy_provider)
        with patch("authentik.outposts.signals.outpost_send_update.send_with_options") as sender:
            with self.captureOnCommitCallbacks(execute=True):
                provider.secret.rotate()
                sender.assert_not_called()
        self.assertCountEqual(
            [call.kwargs["args"] for call in sender.call_args_list],
            [(outpost.pk,), (proxy_outpost.pk,)],
        )

    def test_api_create_with_secret_reference(self):
        """The API accepts a reference to an existing secret"""
        secret = Secret.objects.create(name=generate_id())
        response = self.client.post(
            reverse("authentik_api:radiusprovider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "secret": secret.pk,
            },
        )
        self.assertEqual(response.status_code, 201, response.content)
        provider = RadiusProvider.objects.get(pk=response.json()["pk"])
        self.assertEqual(provider.secret, secret)
        self.assertEqual(provider.secret.value, secret.value)

    def test_outpost_config_shared_secret(self):
        """The outpost config endpoint returns the value for the outpost to use"""
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        response = self.client.get(reverse("authentik_api:radiusprovideroutpost-list"))
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["shared_secret"], provider.secret.value)
