from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert
from authentik.enterprise.providers.ssf.models import SSFProvider, Stream
from authentik.lib.generators import generate_id


class TestStream(APITestCase):
    def setUp(self):
        self.application = Application.objects.create(name=generate_id(), slug=generate_id())
        self.provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=create_test_cert(),
            backchannel_application=self.application,
        )

    def test_stream_add(self):
        """test stream add"""
        res = self.client.post(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "iss": "https://screw-fotos-bracelets-longitude.trycloudflare.com/.well-known/ssf-configuration/abm-ssf/5",
                "aud": [
                    "https://app.authentik.company"
                ],
                "delivery": {
                    "method": "https://schemas.openid.net/secevent/risc/delivery-method/push",
                    "endpoint_url": "https://app.authentik.company",
                },
                "events_requested": [
                    "https://schemas.openid.net/secevent/caep/event-type/credential-change",
                    "https://schemas.openid.net/secevent/caep/event-type/session-revoked",
                ],
                "format": "iss_sub",
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 201)

    def test_stream_delete(self):
        """delete stream"""
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.delete(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Stream.objects.filter(pk=stream.pk).exists())
