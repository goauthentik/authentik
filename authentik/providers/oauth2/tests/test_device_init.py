"""Device init tests"""
from urllib.parse import urlencode

from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import DeviceToken, OAuth2Provider
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.device_init import QS_KEY_CODE


class TesOAuth2DeviceInit(OAuthTestCase):
    """Test device init"""

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
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.device_flow = create_test_flow()
        self.brand = create_test_brand()
        self.brand.flow_device_code = self.device_flow
        self.brand.save()

    def test_device_init(self):
        """Test device init"""
        res = self.client.get(reverse("authentik_providers_oauth2_root:device-login"))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res.url,
            reverse(
                "authentik_core:if-flow",
                kwargs={
                    "flow_slug": self.device_flow.slug,
                },
            ),
        )

    def test_no_flow(self):
        """Test no flow"""
        self.brand.flow_device_code = None
        self.brand.save()
        res = self.client.get(reverse("authentik_providers_oauth2_root:device-login"))
        self.assertEqual(res.status_code, 404)

    def test_device_init_qs(self):
        """Test device init"""
        token = DeviceToken.objects.create(
            user_code="foo",
            provider=self.provider,
        )
        res = self.client.get(
            reverse("authentik_providers_oauth2_root:device-login")
            + "?"
            + urlencode({QS_KEY_CODE: token.user_code})
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res.url,
            reverse(
                "authentik_core:if-flow",
                kwargs={
                    "flow_slug": self.provider.authorization_flow.slug,
                },
            )
            + "?"
            + urlencode({QS_KEY_CODE: token.user_code}),
        )
