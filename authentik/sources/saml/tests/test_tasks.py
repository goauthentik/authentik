"""SAML Source task tests"""

from unittest.mock import patch

from django.test import TestCase
from requests_mock import Mocker

from authentik.core.tests.utils import create_test_flow
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.tasks import update_saml_source_metadata


class TestUpdateSAMLSourceMetadata(TestCase):
    """Tests for update_saml_source_metadata task"""

    url = "http://idp.example.com/saml/metadata"

    def setUp(self):
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            sso_url="https://old.company/sso",
            pre_authentication_flow=create_test_flow(),
            metadata_url=self.url,
        )

    @Mocker()
    def test_updates_changed_settings(self, mock: Mocker):
        """Test that settings defined by the metadata are updated"""
        mock.get(self.url, text=load_fixture("fixtures/idp_metadata.xml"))
        update_saml_source_metadata.send(self.source.pk)
        self.source.refresh_from_db()
        self.assertEqual(self.source.sso_url, "https://saml.company/login/saml/")
        self.assertEqual(self.source.slo_url, "https://saml.company/logout/saml/")
        self.assertIsNotNone(self.source.verification_kp)

    @Mocker()
    def test_updates_all_sources(self, mock: Mocker):
        """Test that the task handles every enabled source with a metadata URL when run
        without arguments, and leaves disabled sources and sources without a URL alone"""
        other_url = "http://idp2.example.com/saml/metadata"
        other = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            sso_url="https://old2.company/sso",
            pre_authentication_flow=create_test_flow(),
            metadata_url=other_url,
        )
        plain = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            sso_url="https://plain.company/sso",
            pre_authentication_flow=create_test_flow(),
        )
        disabled = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            sso_url="https://disabled.company/sso",
            pre_authentication_flow=create_test_flow(),
            metadata_url=other_url,
            enabled=False,
        )
        mock.get(self.url, text=load_fixture("fixtures/idp_metadata.xml"))
        mock.get(other_url, text=load_fixture("fixtures/idp_metadata_simple.xml"))
        update_saml_source_metadata.send()
        self.source.refresh_from_db()
        other.refresh_from_db()
        plain.refresh_from_db()
        disabled.refresh_from_db()
        self.assertEqual(self.source.sso_url, "https://saml.company/login/saml/")
        self.assertEqual(other.sso_url, "https://other.company/sso")
        self.assertEqual(plain.sso_url, "https://plain.company/sso")
        self.assertEqual(disabled.sso_url, "https://disabled.company/sso")

    @Mocker()
    def test_unchanged(self, mock: Mocker):
        """Test that unchanged metadata does not save the source"""
        mock.get(self.url, text=load_fixture("fixtures/idp_metadata.xml"))
        update_saml_source_metadata.send(self.source.pk)
        with patch("authentik.sources.saml.models.SAMLSource.save") as save:
            update_saml_source_metadata.send(self.source.pk)
            save.assert_not_called()

    @Mocker()
    def test_fetch_failure_creates_event(self, mock: Mocker):
        """Test that a failed download leaves the source untouched and logs an event"""
        mock.get(self.url, status_code=404)
        update_saml_source_metadata.send(self.source.pk)
        self.source.refresh_from_db()
        self.assertEqual(self.source.sso_url, "https://old.company/sso")
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.CONFIGURATION_ERROR,
                context__message__icontains="Failed to update SAML source",
            ).exists()
        )

    @Mocker()
    def test_invalid_metadata_creates_event(self, mock: Mocker):
        """Test that invalid metadata leaves the source untouched and logs an event"""
        mock.get(self.url, text="<foo></foo>")
        update_saml_source_metadata.send(self.source.pk)
        self.source.refresh_from_db()
        self.assertEqual(self.source.sso_url, "https://old.company/sso")
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.CONFIGURATION_ERROR,
                context__message__icontains="Failed to update SAML source",
            ).exists()
        )
