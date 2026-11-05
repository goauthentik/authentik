"""Test storing multiple ACS URLs for SAML providers"""

from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import SAMLACSURL, SAMLACSURLMatchingMode, SAMLProvider

DEFAULT = "https://sp.example.com/acs"
SECOND = "https://sp.example.com/acs/second"
REGEX = r"https://[a-z0-9-]+\.tenant\.example\.com/saml/acs"


def create_provider(**kwargs) -> SAMLProvider:
    """Create a provider with a default, a second strict and a regex ACS URL"""
    provider = SAMLProvider(
        name=generate_id(),
        authorization_flow=create_test_flow(),
        **kwargs,
    )
    provider.acs_urls = [
        SAMLACSURL(url=SECOND, index=2),
        SAMLACSURL(url=DEFAULT, index=1, is_default=True),
        SAMLACSURL(url=REGEX, matching_mode=SAMLACSURLMatchingMode.REGEX),
    ]
    provider.save()
    return provider


class TestSAMLProviderACSURLs(TestCase):
    """Test storing ACS URLs on the model"""

    def setUp(self):
        self.provider = create_provider()

    def test_default(self):
        """Test that the entry marked as default is used, regardless of order"""
        self.assertEqual(self.provider.acs_url, DEFAULT)

    def test_default_first_strict(self):
        """Test that without an explicit default, the first strict entry is used"""
        self.provider.acs_urls = [
            SAMLACSURL(url=REGEX, matching_mode=SAMLACSURLMatchingMode.REGEX),
            SAMLACSURL(url=SECOND),
            SAMLACSURL(url=DEFAULT),
        ]
        self.assertEqual(self.provider.acs_url, SECOND)

    def test_default_none(self):
        """Test a provider without any ACS URL"""
        provider = SAMLProvider(name=generate_id())
        self.assertEqual(provider.acs_url, "")

    def test_set_acs_url(self):
        """Test that setting `acs_url` only changes the default entry"""
        self.provider.acs_url = "https://sp.example.com/new"
        self.provider.save()
        self.provider.refresh_from_db()
        self.assertEqual(
            [entry.url for entry in self.provider.acs_urls],
            [SECOND, "https://sp.example.com/new", REGEX],
        )
        self.assertEqual(self.provider.acs_url, "https://sp.example.com/new")

    def test_set_acs_url_empty(self):
        """Test that setting `acs_url` without any entries creates a default entry"""
        provider = SAMLProvider(name=generate_id(), acs_url=DEFAULT)
        self.assertEqual(provider.acs_urls, [SAMLACSURL(url=DEFAULT, is_default=True)])

    def test_legacy_acs_url(self):
        """Test that the deprecated `acs_url` column is kept in sync with the default ACS URL"""
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.legacy_acs_url, DEFAULT)
        self.provider.acs_urls = [SAMLACSURL(url=SECOND, is_default=True)]
        self.provider.save(update_fields=["_acs_urls"])
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.legacy_acs_url, SECOND)


class TestLegacyACSURLWrites(TestCase):
    """Exercise the SQL issued by instances running before migration 0025."""

    @classmethod
    def setUpTestData(cls):
        old_apps = (
            MigrationLoader(connection)
            .project_state(
                [("authentik_providers_saml", "0024_samlprovider_jwt_federation_providers")]
            )
            .apps
        )
        cls.old_provider_model = old_apps.get_model("authentik_providers_saml", "SAMLProvider")

    def test_old_insert(self):
        """An old instance can insert a provider without supplying the new JSON column."""
        old = self.old_provider_model.objects.create(name=generate_id(), acs_url=DEFAULT)
        provider = SAMLProvider.objects.get(pk=old.pk)
        self.assertEqual(provider.acs_urls, [SAMLACSURL(url=DEFAULT, is_default=True)])
        self.assertEqual(provider.acs_url, DEFAULT)
        self.assertTrue(
            SAMLProvider.objects.filter(_acs_urls__contains=[{"url": DEFAULT}]).exists()
        )

    def test_old_update_preserves_other_entries(self):
        """An old URL edit replaces only the selected default, retaining its index."""
        provider = create_provider()
        new_url = "https://sp.example.com/new"
        self.old_provider_model.objects.filter(pk=provider.pk).update(acs_url=new_url)
        provider.refresh_from_db()
        self.assertEqual(provider.acs_url, new_url)
        self.assertEqual(provider.default_acs_url.index, 1)
        self.assertEqual([entry.url for entry in provider.acs_urls], [SECOND, new_url, REGEX])
        provider.name = generate_id()
        provider.save()
        old = self.old_provider_model.objects.get(pk=provider.pk)
        self.assertEqual(old.acs_url, new_url)

    def test_old_update_implicit_default(self):
        """Without an explicit default, an old edit changes the first strict entry."""
        provider = create_provider()
        provider.acs_urls = [
            SAMLACSURL(url=REGEX, matching_mode=SAMLACSURLMatchingMode.REGEX),
            SAMLACSURL(url=SECOND, index=2),
            SAMLACSURL(url=DEFAULT, index=1),
        ]
        provider.save()
        self.old_provider_model.objects.filter(pk=provider.pk).update(acs_url=DEFAULT)
        provider.refresh_from_db()
        self.assertEqual(provider.acs_urls[0].url, REGEX)
        self.assertEqual(provider.default_acs_url, SAMLACSURL(url=DEFAULT, index=2))

    def test_new_list_update_is_visible_to_old_instances(self):
        """New writes select the same default for old and new instances."""
        provider = create_provider()
        provider.acs_urls = [SAMLACSURL(url=SECOND, index=2, is_default=True)]
        provider.save(update_fields=["_acs_urls"])
        self.assertEqual(self.old_provider_model.objects.get(pk=provider.pk).acs_url, SECOND)


class TestSAMLProviderACSURLsAPI(APITestCase):
    """Test the deprecated `acs_url` API field with multiple ACS URLs"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def create(self, **data):
        return self.client.post(
            reverse("authentik_api:samlprovider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                **data,
            },
            format="json",
        )

    def test_create_legacy(self):
        """Test creating a provider with only the deprecated `acs_url` field"""
        response = self.create(acs_url=DEFAULT)
        self.assertEqual(response.status_code, 201, response.content)
        provider = SAMLProvider.objects.get(pk=response.json()["pk"])
        self.assertEqual(provider.acs_urls, [SAMLACSURL(url=DEFAULT, is_default=True)])

    def test_update_legacy(self):
        """Test that updating `acs_url` keeps other ACS URLs"""
        provider = create_provider()
        response = self.client.patch(
            reverse("authentik_api:samlprovider-detail", kwargs={"pk": provider.pk}),
            data={"acs_url": "https://sp.example.com/new"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        provider.refresh_from_db()
        self.assertEqual(
            [entry.url for entry in provider.acs_urls],
            [SECOND, "https://sp.example.com/new", REGEX],
        )

    def test_filter(self):
        """Test filtering providers by any of their ACS URLs"""
        provider = create_provider()
        create_provider()
        SAMLProvider.objects.create(name=generate_id(), acs_url="https://other.example.com")
        response = self.client.get(
            reverse("authentik_api:samlprovider-list"), data={"acs_url": DEFAULT}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(provider.pk, [result["pk"] for result in response.json()["results"]])
        self.assertEqual(response.json()["pagination"]["count"], 2)
