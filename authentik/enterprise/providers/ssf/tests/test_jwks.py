"""JWKS tests"""

import base64
import json

from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_der_x509_certificate
from django.test import TestCase
from django.urls.base import reverse
from jwt import PyJWKSet

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert
from authentik.enterprise.providers.ssf.models import SSFProvider
from authentik.lib.generators import generate_id


class TestJWKS(TestCase):
    """Test JWKS view"""

    def test_rs256(self):
        """Test JWKS request with RS256"""
        provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=create_test_cert(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        app.backchannel_providers.add(provider)
        response = self.client.get(
            reverse("authentik_providers_ssf:jwks", kwargs={"application_slug": app.slug})
        )
        body = json.loads(response.content.decode())
        self.assertEqual(len(body["keys"]), 1)
        PyJWKSet.from_dict(body)
        key = body["keys"][0]
        load_der_x509_certificate(base64.b64decode(key["x5c"][0]), default_backend()).public_key()

    def test_es256(self):
        """Test JWKS request with ES256"""
        provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=create_test_cert(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        app.backchannel_providers.add(provider)
        response = self.client.get(
            reverse("authentik_providers_ssf:jwks", kwargs={"application_slug": app.slug})
        )
        body = json.loads(response.content.decode())
        self.assertEqual(len(body["keys"]), 1)
        PyJWKSet.from_dict(body)
