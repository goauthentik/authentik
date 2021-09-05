"""SAML Provider API Tests"""
from tempfile import TemporaryFile

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, User
from authentik.flows.models import Flow, FlowDesignation
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.tests.test_metadata import METADATA_SIMPLE


class TestSAMLProviderAPI(APITestCase):
    """SAML Provider API Tests"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.get(username="akadmin")
        self.client.force_login(self.user)

    def test_metadata(self):
        """Test metadata export (normal)"""
        self.client.logout()
        provider = SAMLProvider.objects.create(
            name="test",
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
        )
        Application.objects.create(name="test", provider=provider, slug="test")
        response = self.client.get(
            reverse("authentik_api:samlprovider-metadata", kwargs={"pk": provider.pk}),
        )
        self.assertEqual(200, response.status_code)

    def test_metadata_download(self):
        """Test metadata export (download)"""
        self.client.logout()
        provider = SAMLProvider.objects.create(
            name="test",
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
        )
        Application.objects.create(name="test", provider=provider, slug="test")
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
            name="test",
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
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
            metadata.write(METADATA_SIMPLE.encode())
            metadata.seek(0)
            response = self.client.post(
                reverse("authentik_api:samlprovider-import-metadata"),
                {
                    "file": metadata,
                    "name": "test",
                    "authorization_flow": Flow.objects.filter(
                        designation=FlowDesignation.AUTHORIZATION
                    )
                    .first()
                    .slug,
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
                    "name": "test",
                    "authorization_flow": Flow.objects.filter(
                        designation=FlowDesignation.AUTHORIZATION
                    )
                    .first()
                    .slug,
                },
                format="multipart",
            )
        self.assertEqual(400, response.status_code)

    def test_import_invalid(self):
        """Test metadata import (invalid input)"""
        response = self.client.post(
            reverse("authentik_api:samlprovider-import-metadata"),
            {
                "name": "test",
            },
            format="multipart",
        )
        self.assertEqual(400, response.status_code)
