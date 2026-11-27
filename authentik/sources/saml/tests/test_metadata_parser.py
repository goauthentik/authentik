"""SAML Source IdP metadata parser tests"""

from django.test import TestCase

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.sources.saml.models import SAMLBindingTypes, SAMLNameIDPolicy, SAMLSource
from authentik.sources.saml.processors.metadata_parser import IdentityProviderMetadataParser


class TestIdentityProviderMetadataParser(TestCase):
    """Test IdentityProviderMetadataParser"""

    def setUp(self):
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            sso_url="https://old.company/sso",
            pre_authentication_flow=create_test_flow(),
        )

    def test_parse(self):
        """Test parsing an IdP metadata document"""
        metadata = IdentityProviderMetadataParser().parse(load_fixture("fixtures/idp_metadata.xml"))
        self.assertEqual(metadata.entity_id, "https://saml.company/idp")
        # Redirect is preferred over POST regardless of the order in the document
        self.assertEqual(metadata.sso_location, "https://saml.company/login/saml/")
        self.assertEqual(metadata.slo_location, "https://saml.company/logout/saml/")
        self.assertEqual(
            metadata.name_id_formats, [SAMLNameIDPolicy.PERSISTENT, SAMLNameIDPolicy.EMAIL]
        )
        self.assertIsNotNone(metadata.signing_keypair)
        self.assertIn(
            "MIIFUzCCAzugAwIBAgIRAL6tbNcE9Ej9gNlbGKswfFMwDQYJKoZIhvcNAQELBQAw",
            metadata.signing_keypair.certificate_data,
        )

    def test_parse_unsupported_binding_skipped(self):
        """Test that endpoints with unsupported bindings are skipped"""
        metadata = IdentityProviderMetadataParser().parse(
            load_fixture("fixtures/idp_metadata_simple.xml")
        )
        self.assertEqual(metadata.sso_location, "https://other.company/sso")
        self.assertEqual(metadata.sso_binding, "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST")
        self.assertIsNone(metadata.slo_location)
        self.assertIsNone(metadata.signing_keypair)
        self.assertEqual(metadata.name_id_formats, [SAMLNameIDPolicy.EMAIL])

    def test_parse_no_idp(self):
        """Test parsing SP metadata fails"""
        with self.assertRaises(ValueError):
            IdentityProviderMetadataParser().parse(
                load_fixture("fixtures/idp_metadata.xml").replace(
                    "IDPSSODescriptor", "SPSSODescriptor"
                )
            )

    def test_apply_to_source(self):
        """Test applying metadata to a source, including creating the verification certificate"""
        metadata = IdentityProviderMetadataParser().parse(load_fixture("fixtures/idp_metadata.xml"))
        keypair_count = CertificateKeyPair.objects.count()
        self.assertTrue(metadata.apply_to_source(self.source))
        self.source.save()
        self.source.refresh_from_db()
        self.assertEqual(self.source.sso_url, "https://saml.company/login/saml/")
        self.assertEqual(self.source.slo_url, "https://saml.company/logout/saml/")
        self.assertEqual(self.source.binding_type, SAMLBindingTypes.REDIRECT)
        self.assertEqual(self.source.name_id_policy, SAMLNameIDPolicy.PERSISTENT)
        self.assertEqual(CertificateKeyPair.objects.count(), keypair_count + 1)
        self.assertEqual(
            self.source.verification_kp.name,
            f"Source {self.source.name} - SAML Signing Certificate",
        )
        # Applying the same metadata again changes nothing
        metadata = IdentityProviderMetadataParser().parse(load_fixture("fixtures/idp_metadata.xml"))
        self.assertFalse(metadata.apply_to_source(self.source))

    def test_apply_name_id_policy(self):
        """Test that the NameID policy is only replaced when the IdP doesn't support it"""
        # PERSISTENT (the default) is supported by idp_metadata.xml, so it is kept
        metadata = IdentityProviderMetadataParser().parse(load_fixture("fixtures/idp_metadata.xml"))
        metadata.apply_to_source(self.source)
        self.assertEqual(self.source.name_id_policy, SAMLNameIDPolicy.PERSISTENT)
        # idp_metadata_simple.xml only supports EMAIL, so the policy is replaced
        metadata = IdentityProviderMetadataParser().parse(
            load_fixture("fixtures/idp_metadata_simple.xml")
        )
        metadata.apply_to_source(self.source)
        self.assertEqual(self.source.name_id_policy, SAMLNameIDPolicy.EMAIL)

    def test_apply_keeps_post_auto(self):
        """Test that the auto-submitting POST binding chosen by an admin is kept"""
        self.source.binding_type = SAMLBindingTypes.POST_AUTO
        metadata = IdentityProviderMetadataParser().parse(
            load_fixture("fixtures/idp_metadata_simple.xml")
        )
        metadata.apply_to_source(self.source)
        self.assertEqual(self.source.binding_type, SAMLBindingTypes.POST_AUTO)

    def test_apply_updates_certificate_in_place(self):
        """Test that a rotated certificate updates the existing keypair"""
        old_cert = create_test_cert()
        self.source.verification_kp = old_cert
        self.source.save()
        keypair_count = CertificateKeyPair.objects.count()
        metadata = IdentityProviderMetadataParser().parse(load_fixture("fixtures/idp_metadata.xml"))
        self.assertTrue(metadata.apply_to_source(self.source))
        self.source.save()
        self.source.refresh_from_db()
        self.assertEqual(self.source.verification_kp.pk, old_cert.pk)
        self.assertEqual(CertificateKeyPair.objects.count(), keypair_count)
        self.assertIn(
            "MIIFUzCCAzugAwIBAgIRAL6tbNcE9Ej9gNlbGKswfFMwDQYJKoZIhvcNAQELBQAw",
            self.source.verification_kp.certificate_data,
        )
