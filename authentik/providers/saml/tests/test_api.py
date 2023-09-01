"""SAML Provider API Tests"""
from json import loads
from tempfile import TemporaryFile

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowDesignation
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider


class TestSAMLProviderAPI(APITestCase):
    """SAML Provider API Tests"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_detail(self):
        """Test detail"""
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        Application.objects.create(name=generate_id(), provider=provider, slug=generate_id())
        response = self.client.get(
            reverse("authentik_api:samlprovider-detail", kwargs={"pk": provider.pk}),
        )
        self.assertEqual(200, response.status_code)

    def test_metadata(self):
        """Test metadata export (normal)"""
        self.client.logout()
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        Application.objects.create(name=generate_id(), provider=provider, slug=generate_id())
        response = self.client.get(
            reverse("authentik_api:samlprovider-metadata", kwargs={"pk": provider.pk}),
        )
        self.assertEqual(200, response.status_code)

    def test_metadata_download(self):
        """Test metadata export (download)"""
        self.client.logout()
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        Application.objects.create(name=generate_id(), provider=provider, slug=generate_id())
        response = self.client.get(
            reverse("authentik_api:samlprovider-metadata", kwargs={"pk": provider.pk})
            + "?download",
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("Content-Disposition", response)

    def test_metadata_invalid(self):
        """Test metadata export (invalid)"""
        self.client.logout()
        # Provider without application
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        response = self.client.get(
            reverse("authentik_api:samlprovider-metadata", kwargs={"pk": provider.pk}),
        )
        self.assertEqual(200, response.status_code)
        response = self.client.get(
            reverse("authentik_api:samlprovider-metadata", kwargs={"pk": "abc"}),
        )
        self.assertEqual(404, response.status_code)

    def test_import_success(self):
        """Test metadata import (success case)"""
        with TemporaryFile() as metadata:
            metadata.write(load_fixture("fixtures/simple.xml").encode())
            metadata.seek(0)
            response = self.client.post(
                reverse("authentik_api:samlprovider-import-metadata"),
                {
                    "file": metadata,
                    "name": generate_id(),
                    "authorization_flow": create_test_flow(FlowDesignation.AUTHORIZATION).pk,
                },
                format="multipart",
            )
        self.assertEqual(204, response.status_code)
        # We don't test the actual object being created here, that has its own tests

    def test_import_failed(self):
        """Test metadata import (invalid xml)"""
        with TemporaryFile() as metadata:
            metadata.write(b"invalid")
            metadata.seek(0)
            response = self.client.post(
                reverse("authentik_api:samlprovider-import-metadata"),
                {
                    "file": metadata,
                    "name": generate_id(),
                    "authorization_flow": create_test_flow().pk,
                },
                format="multipart",
            )
        self.assertEqual(400, response.status_code)

    def test_import_invalid(self):
        """Test metadata import (invalid input)"""
        response = self.client.post(
            reverse("authentik_api:samlprovider-import-metadata"),
            {
                "name": generate_id(),
            },
            format="multipart",
        )
        self.assertEqual(400, response.status_code)

    @apply_blueprint("system/providers-saml.yaml")
    def test_preview(self):
        """Test Preview API Endpoint"""
        provider: SAMLProvider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        Application.objects.create(name=generate_id(), provider=provider, slug=generate_id())
        response = self.client.get(
            reverse("authentik_api:samlprovider-preview-user", kwargs={"pk": provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())["preview"]["attributes"]
        self.assertEqual(
            [x for x in body if x["Name"] == "http://schemas.goauthentik.io/2021/02/saml/username"][
                0
            ]["Value"],
            [self.user.username],
        )
