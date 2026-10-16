"""SAML Source API tests"""

from django.urls import reverse
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.sources.saml.models import SAMLBindingTypes, SAMLNameIDPolicy, SAMLSource


class TestSAMLSourceAPI(APITestCase):
    """SAML Source API tests"""

    url = "http://idp.example.com/saml/metadata"

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.flow = create_test_flow()

    def _payload(self, **extra) -> dict:
        return {
            "name": generate_id(),
            "slug": generate_id(),
            "pre_authentication_flow": str(self.flow.pk),
            **extra,
        }

    @Mocker()
    def test_create_from_metadata_url(self, mock: Mocker):
        """Test creating a source with only a metadata URL fills in the IdP settings"""
        mock.get(self.url, text=load_fixture("fixtures/idp_metadata.xml"))
        response = self.client.post(
            reverse("authentik_api:samlsource-list"), self._payload(metadata_url=self.url)
        )
        self.assertEqual(response.status_code, 201, response.content)
        source = SAMLSource.objects.get(pk=response.json()["pk"])
        self.assertEqual(source.metadata_url, self.url)
        self.assertEqual(source.sso_url, "https://saml.company/login/saml/")
        self.assertEqual(source.slo_url, "https://saml.company/logout/saml/")
        self.assertEqual(source.binding_type, SAMLBindingTypes.REDIRECT)
        self.assertEqual(source.name_id_policy, SAMLNameIDPolicy.PERSISTENT)
        self.assertIsNotNone(source.verification_kp)

    @Mocker()
    def test_create_from_metadata_url_blank_sso_url(self, mock: Mocker):
        """Test creating a source with a metadata URL and an empty SSO URL, as the form sends"""
        mock.get(self.url, text=load_fixture("fixtures/idp_metadata.xml"))
        response = self.client.post(
            reverse("authentik_api:samlsource-list"),
            self._payload(metadata_url=self.url, sso_url="", slo_url=""),
        )
        self.assertEqual(response.status_code, 201, response.content)
        source = SAMLSource.objects.get(pk=response.json()["pk"])
        self.assertEqual(source.sso_url, "https://saml.company/login/saml/")

    def test_create_requires_sso_url_or_metadata_url(self):
        """Test creating a source without an SSO URL or metadata URL fails"""
        response = self.client.post(reverse("authentik_api:samlsource-list"), self._payload())
        self.assertEqual(response.status_code, 400)
        self.assertIn("sso_url", response.json())
        response = self.client.post(
            reverse("authentik_api:samlsource-list"), self._payload(sso_url="", metadata_url="")
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("sso_url", response.json())

    @Mocker()
    def test_create_invalid_metadata_url(self, mock: Mocker):
        """Test that a metadata URL that can't be fetched or parsed fails validation"""
        mock.get(self.url, status_code=500)
        response = self.client.post(
            reverse("authentik_api:samlsource-list"), self._payload(metadata_url=self.url)
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("metadata_url", response.json())
        mock.get(self.url, text="<foo></foo>")
        response = self.client.post(
            reverse("authentik_api:samlsource-list"), self._payload(metadata_url=self.url)
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("metadata_url", response.json())

    @Mocker()
    def test_update_metadata_url(self, mock: Mocker):
        """Test setting a metadata URL on an existing source applies the metadata"""
        source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            sso_url="https://old.company/sso",
            pre_authentication_flow=self.flow,
        )
        mock.get(self.url, text=load_fixture("fixtures/idp_metadata_simple.xml"))
        response = self.client.patch(
            reverse("authentik_api:samlsource-detail", kwargs={"slug": source.slug}),
            {"metadata_url": self.url},
        )
        self.assertEqual(response.status_code, 200, response.content)
        source.refresh_from_db()
        self.assertEqual(source.sso_url, "https://other.company/sso")
        self.assertEqual(source.binding_type, SAMLBindingTypes.POST)
        # An unchanged URL is not fetched again
        mock.reset_mock()
        response = self.client.patch(
            reverse("authentik_api:samlsource-detail", kwargs={"slug": source.slug}),
            {"metadata_url": self.url, "name": generate_id()},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(mock.call_count, 0)
