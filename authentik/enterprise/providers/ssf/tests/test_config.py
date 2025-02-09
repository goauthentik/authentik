import json

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert
from authentik.enterprise.providers.ssf.models import (
    SSFProvider,
)
from authentik.lib.generators import generate_id


class TestConfiguration(APITestCase):
    def setUp(self):
        self.application = Application.objects.create(name=generate_id(), slug=generate_id())
        self.provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=create_test_cert(),
            backchannel_application=self.application,
        )

    def test_config_fetch(self):
        """test SSF configuration (unauthenticated)"""
        res = self.client.get(
            reverse(
                "authentik_providers_ssf:configuration",
                kwargs={"application_slug": self.application.slug},
            ),
        )
        self.assertEqual(res.status_code, 200)
        content = json.loads(res.content)
        self.assertEqual(content["spec_version"], "1_0-ID2")

    def test_config_fetch_authenticated(self):
        """test SSF configuration (authenticated)"""
        res = self.client.get(
            reverse(
                "authentik_providers_ssf:configuration",
                kwargs={"application_slug": self.application.slug},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 200)
        content = json.loads(res.content)
        self.assertEqual(content["spec_version"], "1_0-ID2")
