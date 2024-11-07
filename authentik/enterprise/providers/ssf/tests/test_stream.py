from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert
from authentik.enterprise.providers.ssf.models import SSFProvider
from authentik.lib.generators import generate_id


class TestStream(APITestCase):
    def setUp(self):
        self.provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=create_test_cert(),
        )
        self.application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider
        )

    def test_stream_add(self):
        """test stream add"""
        res = self.client.post(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug, "provider": self.provider.pk},
            ),
            data={
                "iss": "https://screw-fotos-bracelets-longitude.trycloudflare.com/.well-known/ssf-configuration/abm-ssf/5",
                "aud": [
                    "https://federation.apple.com/feeds/business/caep/2034455812/871ada94-90f6-4cdc-9996-a9dd8d62ef14"
                ],
                "delivery": {
                    "method": "https://schemas.openid.net/secevent/risc/delivery-method/push",
                    "endpoint_url": "https://federation.apple.com/feeds/business/caep/2034455812/871ada94-90f6-4cdc-9996-a9dd8d62ef14",
                },
                "events_requested": [
                    "https://schemas.openid.net/secevent/caep/event-type/credential-change",
                    "https://schemas.openid.net/secevent/caep/event-type/session-revoked",
                ],
                "format": "iss_sub",
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        print(res)
        print(res.content)
        self.assertEqual(res.status_code, 200)
