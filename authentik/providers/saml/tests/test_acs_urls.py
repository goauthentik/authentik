"""Test storing multiple ACS URLs for SAML providers"""

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
