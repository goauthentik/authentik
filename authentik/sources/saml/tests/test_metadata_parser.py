"""Test Identity-Provider Metadata Parser"""

from base64 import b64encode

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate
from django.test import RequestFactory, TestCase
from lxml import etree  # nosec

from authentik.common.saml.constants import NS_MAP
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.crypto.models import CertificateKeyPair, CertificateKeyPairRing, KeyPairRef
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.lib.xml import lxml_from_string
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.sources.saml.models import SAMLNameIDPolicy
from authentik.sources.saml.processors.metadata_parser import (
    APPLY_POLICY_FORCE,
    APPLY_POLICY_IF_NOT_DEVIATED,
    IdentityProviderMetadataParser,
)


def _pem_to_der_b64(pem: str) -> str:
    """Convert PEM cert to base64(DER) string suitable for <ds:X509Certificate>."""
    cert = load_pem_x509_certificate(pem.encode("utf-8"), default_backend())
    der = cert.public_bytes(serialization.Encoding.DER)
    return b64encode(der).decode("ascii")


def _build_multi_cert_idp_metadata_xml(
    *,
    entity_id: str,
    sso_post: str,
    sso_redirect: str,
    slo_post: str,
    slo_redirect: str,
    cert_b64s: list[str],
    cert_b64e: list[str],
) -> str:
    """Build minimal EntityDescriptor XML with IDPSSODescriptor and multiple certs."""

    def kd(use: str, b64: str) -> str:
        return f"""
        <md:KeyDescriptor use="{use}">
          <ds:KeyInfo><ds:X509Data><ds:X509Certificate>{b64}</ds:X509Certificate></ds:X509Data></ds:KeyInfo>
        </md:KeyDescriptor>
        """

    signing = "\n".join(kd("signing", b) for b in cert_b64s)
    encryption = "\n".join(kd("encryption", b) for b in cert_b64e)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor
  xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
  xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
  entityID="{entity_id}"
>
  <md:IDPSSODescriptor
    protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"
    WantAuthnRequestsSigned="true"
  >
    <md:SingleSignOnService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
      Location="{sso_redirect}"
    />
      <md:SingleSignOnService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="{sso_post}"
    />

    <md:SingleLogoutService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
      Location="{slo_redirect}"
    />
    <md:SingleLogoutService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="{slo_post}"
    />

    <md:NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:persistent</md:NameIDFormat>
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>

    {signing}
    {encryption}
  </md:IDPSSODescriptor>
</md:EntityDescriptor>
"""


def _build_simple_idp_entity_descriptor(*, entity_id: str, sso_url: str) -> str:
    """Build minimal IdP EntityDescriptor fragment."""
    return f"""
<md:EntityDescriptor entityID="{entity_id}">
  <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:SingleSignOnService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
      Location="{sso_url}"
    />
  </md:IDPSSODescriptor>
</md:EntityDescriptor>
"""


def _build_simple_sp_entity_descriptor(*, entity_id: str, acs_url: str) -> str:
    """Build minimal SP EntityDescriptor fragment."""
    return f"""
<md:EntityDescriptor entityID="{entity_id}">
  <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:AssertionConsumerService
      index="0"
      isDefault="true"
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="{acs_url}"
    />
  </md:SPSSODescriptor>
</md:EntityDescriptor>
"""


class TestIdentityProviderMetadataParserMultiCert(TestCase):
    def setUp(self) -> None:
        self.flow = create_test_flow()
        self.kp1 = create_test_cert(PrivateKeyAlg.RSA)
        self.kp2 = create_test_cert(PrivateKeyAlg.RSA)

        cert_b64s = [
            _pem_to_der_b64(self.kp1.certificate_data),
            _pem_to_der_b64(self.kp2.certificate_data),
        ]

        self.xml = _build_multi_cert_idp_metadata_xml(
            entity_id="https://idp-multi.example.org/idp",
            sso_post="https://idp-multi.example.org/sso/post",
            sso_redirect="https://idp-multi.example.org/sso/redirect",
            slo_post="https://idp-multi.example.org/slo/post",
            slo_redirect="https://idp-multi.example.org/slo/redirect",
            cert_b64s=cert_b64s,
            cert_b64e=cert_b64s,
        )

    def test_multi_certs_parse_extracts_lists(self):
        meta = IdentityProviderMetadataParser().parse(self.xml)

        self.assertEqual(meta.entity_id, "https://idp-multi.example.org/idp")
        self.assertTrue(meta.want_authn_requests_signed)

        self.assertEqual(meta.sso_binding, "post")
        self.assertEqual(meta.sso_location, "https://idp-multi.example.org/sso/post")
        self.assertEqual(meta.slo_binding, "post")
        self.assertEqual(meta.slo_location, "https://idp-multi.example.org/slo/post")

        self.assertEqual(meta.name_id_policy, SAMLNameIDPolicy.PERSISTENT)

        self.assertIsNotNone(meta.signing_cert_pems)
        self.assertIsNotNone(meta.encryption_cert_pems)
        self.assertEqual(len(meta.signing_cert_pems), 2)
        self.assertEqual(len(meta.encryption_cert_pems), 2)

        self.assertTrue(all(pem.strip() for pem in meta.signing_cert_pems))
        self.assertTrue(all(pem.strip() for pem in meta.encryption_cert_pems))

    def test_simple_idp(self):
        xml = _build_multi_cert_idp_metadata_xml(
            entity_id="https://idp-simple.example.org/idp",
            sso_post="https://idp-simple.example.org/sso/post",
            sso_redirect="https://idp-simple.example.org/sso/redirect",
            slo_post="https://idp-simple.example.org/slo/post",
            slo_redirect="https://idp-simple.example.org/slo/redirect",
            cert_b64s=[],
            cert_b64e=[],
        )

        meta = IdentityProviderMetadataParser().parse(xml)
        self.assertEqual(meta.entity_id, "https://idp-simple.example.org/idp")
        self.assertTrue(meta.want_authn_requests_signed)
        self.assertEqual(meta.name_id_policy, SAMLNameIDPolicy.PERSISTENT)
        self.assertEqual(meta.signing_cert_pems, [])
        self.assertEqual(meta.encryption_cert_pems, [])

    def test_idp_metadata_fixture(self):
        xml = load_fixture("fixtures/idp-metadata.xml")
        meta = IdentityProviderMetadataParser().parse(xml)

        self.assertEqual(meta.entity_id, "https://idp.example.org/idp/shibboleth")

        self.assertEqual(meta.sso_binding, "post")
        self.assertIn("/POST/SSO", meta.sso_location)

        self.assertTrue(meta.slo_location in ("", None))
        self.assertTrue(meta.slo_binding in ("", None))

        # certs
        self.assertEqual(len(meta.signing_cert_pems), 2)
        self.assertEqual(len(meta.encryption_cert_pems), 1)

        self.assertEqual(meta.name_id_policy, SAMLNameIDPolicy.UNSPECIFIED)

    def test_parse_display_name_from_idp_descriptor_extensions(self):
        """Parse should read mdui:DisplayName from IDPSSODescriptor Extensions."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor
  xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
  xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
  entityID="https://idp-display.example.org/idp"
>
  <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:Extensions>
      <mdui:UIInfo>
        <mdui:DisplayName xml:lang="en">Example IdP</mdui:DisplayName>
      </mdui:UIInfo>
    </md:Extensions>
    <md:SingleSignOnService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
      Location="https://idp-display.example.org/sso"
    />
  </md:IDPSSODescriptor>
</md:EntityDescriptor>
"""
        entry = IdentityProviderMetadataParser().parse(xml)
        self.assertEqual(entry.display_name, "Example IdP")


def _signed_idp_metadata(*keypairs: CertificateKeyPair) -> str:
    """Metadata of an authentik SAML provider whose signing ring holds `keypairs`. Every one of
    them is published, and the metadata is signed with the first one that has a private key."""
    ring = CertificateKeyPairRing.objects.create(name=generate_id())
    ring.sync_bindings(
        [KeyPairRef(keypair=keypair, order=order) for order, keypair in enumerate(keypairs)]
    )
    provider = SAMLProvider.objects.create(
        name=generate_id(),
        authorization_flow=create_test_flow(),
        invalidation_flow=create_test_flow(),
        signing_kp_ring=ring,
    )
    Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
    return MetadataProcessor(provider, RequestFactory().get("/")).build_entity_descriptor()


def _certificate_only() -> CertificateKeyPair:
    """A keypair that can't sign, as it has no private key"""
    keypair = create_test_cert()
    keypair.key_data = ""
    keypair.save()
    return keypair


class TestIdentityProviderMetadataSignature(TestCase):
    """Signed IdP metadata"""

    def setUp(self) -> None:
        self.unused = _certificate_only()
        self.signer = create_test_cert()
        self.metadata = _signed_idp_metadata(self.unused, self.signer)

    def test_embedded_certificate(self):
        """Test the signature is verified with whichever published certificate signed it"""
        metadata = IdentityProviderMetadataParser().parse(self.metadata)
        self.assertEqual(
            metadata.signing_cert_pems,
            [self.unused.certificate_data.strip(), self.signer.certificate_data.strip()],
        )

    def test_trust_anchor(self):
        """Test the signature is verified with the given certificate"""
        IdentityProviderMetadataParser(signing_certificate=self.signer).parse(self.metadata)

    def test_wrong_trust_anchor(self):
        """Test metadata not signed by the given certificate is rejected, even though it was
        signed with a certificate it publishes"""
        with self.assertRaisesMessage(ValueError, "Failed to verify Metadata signature"):
            IdentityProviderMetadataParser(signing_certificate=self.unused).parse(self.metadata)

    def test_tampered(self):
        """Test metadata changed after it was signed is rejected"""
        root = lxml_from_string(self.metadata.encode())
        # Serializing it again on its own keeps the signature valid
        IdentityProviderMetadataParser().parse(etree.tostring(root).decode())
        sso = root.xpath("//md:IDPSSODescriptor/md:SingleSignOnService", namespaces=NS_MAP)[0]
        sso.attrib["Location"] = "https://attacker.example.org/sso"
        with self.assertRaisesMessage(ValueError, "Failed to verify Metadata signature"):
            IdentityProviderMetadataParser().parse(etree.tostring(root).decode())

    def test_no_signing_certificate(self):
        """Test signed metadata without a signing certificate to verify it with is rejected"""
        root = lxml_from_string(self.metadata.encode())
        for key_descriptor in root.xpath(
            "//md:IDPSSODescriptor/md:KeyDescriptor[@use='signing']", namespaces=NS_MAP
        ):
            key_descriptor.getparent().remove(key_descriptor)
        with self.assertRaisesMessage(
            ValueError, "Metadata is signed but no signing certificate is present"
        ):
            IdentityProviderMetadataParser().parse(etree.tostring(root).decode())

    def test_check_signature_unsigned(self):
        """Test unsigned metadata passes the signature check, as there's nothing to verify"""
        root = lxml_from_string(load_fixture("fixtures/idp-metadata.xml").encode())
        IdentityProviderMetadataParser().check_signature(root, self.signer)


class TestIdentityProviderMetadataParserEdgeCases(TestCase):
    """Input the parser has to cope with"""

    def test_certificate_listed_twice(self):
        """Test a certificate listed for signing and without a use is only trusted once"""
        certificate = _pem_to_der_b64(create_test_cert().certificate_data)
        key_info = (
            '<ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#"><ds:X509Data>'
            f"<ds:X509Certificate>{certificate}</ds:X509Certificate>"
            "</ds:X509Data></ds:KeyInfo>"
        )
        xml = f"""<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="https://idp.example.org/idp">
  <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:KeyDescriptor use="signing">{key_info}</md:KeyDescriptor>
    <md:KeyDescriptor>{key_info}</md:KeyDescriptor>
    <md:SingleSignOnService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
      Location="https://idp.example.org/sso"
    />
  </md:IDPSSODescriptor>
</md:EntityDescriptor>"""
        metadata = IdentityProviderMetadataParser().parse(xml)
        self.assertEqual(len(metadata.signing_cert_pems), 1)

    def test_invalid_key_descriptor_use(self):
        """Test only signing, encryption, or no use can be asked for"""
        root = lxml_from_string(load_fixture("fixtures/idp-metadata.xml").encode())
        with self.assertRaisesMessage(ValueError, "Invalid use"):
            IdentityProviderMetadataParser().get_keydescriptor_cert_pems(root, use="other")

    def test_to_source_requires_name(self):
        """Test a source can't be created without a name"""
        metadata = IdentityProviderMetadataParser().parse(load_fixture("fixtures/idp-metadata.xml"))
        with self.assertRaisesMessage(ValueError, "Name is required"):
            metadata.to_source(None, pre_authentication_flow=create_test_flow())
