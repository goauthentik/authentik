"""Device backchannel tests"""

from json import loads

from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_flow
from authentik.crypto.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TesOAuth2DeviceBackchannel(OAuthTestCase):
    """Test device back channel"""

    def setUp(self) -> None:
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
        )
        self.application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )

    def test_backchannel_invalid(self):
        """Test backchannel"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": "foo",
            },
        )
        self.assertEqual(res.status_code, 400)
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
        )
        self.assertEqual(res.status_code, 400)
        # test without application
        self.application.provider = None
        self.application.save()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": "test",
            },
        )
        self.assertEqual(res.status_code, 400)

    def test_backchannel(self):
        """Test backchannel"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": self.provider.client_id,
            },
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        self.assertEqual(body["expires_in"], 60)
