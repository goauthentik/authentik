"""Device init tests"""

from urllib.parse import urlencode

from django.urls import reverse
from rest_framework.test import APIClient

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.crypto.generators import generate_id
from authentik.policies.models import PolicyBinding
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

        self.api_client = APIClient()
        self.api_client.force_login(self.user)

    def test_device_init_get(self):
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
            )
            + "?"
            + urlencode({"inspector": "available"}),
        )

    def test_device_init_post(self):
        """Test device init"""
        res = self.api_client.get(reverse("authentik_providers_oauth2_root:device-login"))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res.url,
            reverse(
                "authentik_core:if-flow",
                kwargs={
                    "flow_slug": self.device_flow.slug,
                },
            )
            + "?"
            + urlencode({"inspector": "available"}),
        )
        res = self.api_client.get(
            reverse(
                "authentik_api:flow-executor",
                kwargs={
                    "flow_slug": self.device_flow.slug,
                },
            ),
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content,
            {
                "component": "ak-provider-oauth2-device-code",
                "flow_info": {
                    "background": "/static/dist/assets/images/flow_background.jpg",
                    "cancel_url": "/flows/-/cancel/",
                    "layout": "stacked",
                    "title": self.device_flow.title,
                },
            },
        )

        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        token = DeviceToken.objects.create(
            provider=provider,
        )

        res = self.api_client.post(
            reverse(
                "authentik_api:flow-executor",
                kwargs={
                    "flow_slug": self.device_flow.slug,
                },
            ),
            data={
                "component": "ak-provider-oauth2-device-code",
                "code": token.user_code,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content,
            {
                "component": "xak-flow-redirect",
                "to": reverse(
                    "authentik_core:if-flow",
                    kwargs={
                        "flow_slug": provider.authorization_flow.slug,
                    },
                )
                + "?"
                + urlencode({"inspector": "available"}),
            },
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
            + urlencode({QS_KEY_CODE: token.user_code, "inspector": "available"}),
        )

    def test_device_init_denied(self):
        """Test device init"""
        group = Group.objects.create(name="foo")
        PolicyBinding.objects.create(
            group=group,
            target=self.application,
            order=0,
        )
        token = DeviceToken.objects.create(
            user_code="foo",
            provider=self.provider,
        )
        res = self.client.get(
            reverse("authentik_providers_oauth2_root:device-login")
            + "?"
            + urlencode({QS_KEY_CODE: token.user_code})
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Permission denied", res.content)
