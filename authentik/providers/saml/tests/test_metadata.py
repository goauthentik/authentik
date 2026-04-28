"""Test Service-Provider Metadata Parser"""

from base64 import b64encode

import xmlsec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate
from defusedxml.lxml import fromstring
from django.test import RequestFactory, TestCase
from lxml import etree  # nosec

from authentik.common.saml.constants import ECDSA_SHA256, NS_MAP, NS_SAML_METADATA
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.lib.xml import lxml_from_string
from authentik.providers.saml.models import SAMLBindings, SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.providers.saml.processors.metadata_parser import ServiceProviderMetadataParser
from authentik.providers.saml.utils.keyring import pick_cert_pem
from authentik.sources.saml.models import SAMLNameIDPolicy


def _pem_to_der_b64(pem: str) -> str:
    """Convert PEM cert to base64(DER) string suitable for <ds:X509Certificate>."""
    cert = load_pem_x509_certificate(pem.encode("utf-8"), default_backend())
    der = cert.public_bytes(serialization.Encoding.DER)
    return b64encode(der).decode("ascii")


def _build_multi_cert_sp_metadata_xml(
    *, entity_id: str, acs_url: str, sls_url: str, cert_b64s: list[str], cert_b64e: list[str]
) -> str:
    """Build minimal EntityDescriptor XML with multiple signing/encryption certs."""

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
  <md:SPSSODescriptor
    protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"
    AuthnRequestsSigned="true"
    WantAssertionsSigned="false"
  >
    <md:AssertionConsumerService
      index="0" isDefault="true"
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="{acs_url}"
    />
    <md:SingleLogoutService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="{sls_url}"
    />
    <md:NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:persistent</md:NameIDFormat>
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>

    {signing}
    {encryption}
  </md:SPSSODescriptor>
</md:EntityDescriptor>
"""


class TestServiceProviderMetadataParser(TestCase):
    """Test ServiceProviderMetadataParser parsing and creation of SAML Provider"""

    def setUp(self) -> None:
        self.flow = create_test_flow()
        self.factory = RequestFactory()

    def test_consistent(self):
        """Test that metadata generation is consistent"""
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
        )
        Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=provider,
        )
        request = self.factory.get("/")
        metadata_a = MetadataProcessor(provider, request).build_entity_descriptor()
        metadata_b = MetadataProcessor(provider, request).build_entity_descriptor()
        self.assertEqual(metadata_a, metadata_b)

    def test_schema(self):
        """Test that metadata generation is consistent"""
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
        )
        Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=provider,
        )
        request = self.factory.get("/")
        metadata = lxml_from_string(MetadataProcessor(provider, request).build_entity_descriptor())

        schema = etree.XMLSchema(
            etree.parse(
                source="schemas/saml-schema-metadata-2.0.xsd", parser=etree.XMLParser()
            )  # nosec
        )
        self.assertTrue(schema.validate(metadata))

    def test_schema_want_authn_requests_signed(self):
        """Test metadata generation with WantAuthnRequestsSigned"""
        cert = create_test_cert()
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            verification_kp=cert,
        )
        Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=provider,
        )
        request = self.factory.get("/")
        metadata = lxml_from_string(MetadataProcessor(provider, request).build_entity_descriptor())
        idp_sso_descriptor = metadata.findall(f"{{{NS_SAML_METADATA}}}IDPSSODescriptor")[0]
        self.assertEqual(idp_sso_descriptor.attrib["WantAuthnRequestsSigned"], "true")

    def test_simple(self):
        """Test simple metadata without Signing"""
        metadata = ServiceProviderMetadataParser().parse(load_fixture("fixtures/simple.xml"))
        provider = metadata.to_provider("test", self.flow, self.flow)
        self.assertEqual(provider.acs_url, "http://localhost:8080/saml/acs")
        self.assertEqual(provider.issuer, "http://localhost:8080/saml/metadata")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(provider.default_name_id_policy, SAMLNameIDPolicy.EMAIL)
        self.assertEqual(
            len(provider.property_mappings.all()),
            len(SAMLPropertyMapping.objects.exclude(managed__isnull=True)),
        )

    def test_with_signing_cert(self):
        """Test Metadata with signing cert"""
        create_test_cert()
        metadata = ServiceProviderMetadataParser().parse(load_fixture("fixtures/cert.xml"))
        provider = metadata.to_provider("test", self.flow, self.flow)
        self.assertEqual(provider.acs_url, "http://localhost:8080/apps/user_saml/saml/acs")
        self.assertEqual(provider.issuer, "http://localhost:8080/apps/user_saml/saml/metadata")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(
            pick_cert_pem(kp=provider.verification_kp, ring=provider.verification_kp_ring),
            load_fixture("fixtures/cert.pem"),
        )
        self.assertIsNone(provider.verification_kp)
        self.assertIsNotNone(provider.verification_kp_ring)
        self.assertEqual(provider.audience, "")

    def test_with_signing_cert_invalid_signature(self):
        """Test Metadata with signing cert (invalid signature)"""
        with self.assertRaises(ValueError):
            ServiceProviderMetadataParser().parse(
                load_fixture("fixtures/cert.xml").replace("/apps/user_saml", "")
            )

    def test_signature_rsa(self):
        """Test signature validation (RSA)"""
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            signing_kp=create_test_cert(PrivateKeyAlg.RSA),
        )
        Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=provider,
        )
        request = self.factory.get("/")
        metadata = MetadataProcessor(provider, request).build_entity_descriptor()

        root = fromstring(metadata.encode())
        xmlsec.tree.add_ids(root, ["ID"])
        signature_nodes = root.xpath("/md:EntityDescriptor/ds:Signature", namespaces=NS_MAP)
        signature_node = signature_nodes[0]
        ctx = xmlsec.SignatureContext()
        key = xmlsec.Key.from_memory(
            provider.signing_kp.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
            None,
        )
        ctx.key = key
        ctx.verify(signature_node)

    def test_signature_ecdsa(self):
        """Test signature validation (ECDSA)"""
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            signing_kp=create_test_cert(PrivateKeyAlg.ECDSA),
            signature_algorithm=ECDSA_SHA256,
        )
        Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=provider,
        )
        request = self.factory.get("/")
        metadata = MetadataProcessor(provider, request).build_entity_descriptor()

        root = fromstring(metadata.encode())
        xmlsec.tree.add_ids(root, ["ID"])
        signature_nodes = root.xpath("/md:EntityDescriptor/ds:Signature", namespaces=NS_MAP)
        signature_node = signature_nodes[0]
        ctx = xmlsec.SignatureContext()
        key = xmlsec.Key.from_memory(
            provider.signing_kp.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
            None,
        )
        ctx.key = key
        ctx.verify(signature_node)

    def test_multi_bindings(self):
        """Test metadata including more than one bindings."""
        metadata = ServiceProviderMetadataParser().parse(
            load_fixture("fixtures/multi-bindings.xml")
        )
        provider = metadata.to_provider("test", self.flow, self.flow)
        self.assertEqual(
            provider.acs_url, "https://sp-b.example.org:10446/Shibboleth.sso/SAML2/POST"
        )
        self.assertEqual(provider.issuer, "https://sp-b.example.org/shibboleth")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(provider.default_name_id_policy, SAMLNameIDPolicy.UNSPECIFIED)
        self.assertEqual(
            len(provider.property_mappings.all()),
            len(SAMLPropertyMapping.objects.exclude(managed__isnull=True)),
        )


class TestServiceProviderMetadataParserMultiCert(TestCase):
    def setUp(self) -> None:
        self.flow = create_test_flow()
        self.kp1 = create_test_cert()
        self.kp2 = create_test_cert()

        self.cert_b64s = [
            _pem_to_der_b64(self.kp1.certificate_data),
            _pem_to_der_b64(self.kp2.certificate_data),
        ]

        self.xml = _build_multi_cert_sp_metadata_xml(
            entity_id="https://sp-multi.example.org/shibboleth",
            acs_url="https://sp-multi.example.org/Shibboleth.sso/SAML2/POST",
            sls_url="https://sp-multi.example.org/Shibboleth.sso/Logout",
            cert_b64s=self.cert_b64s,
            cert_b64e=self.cert_b64s,
        )

    def test_multi_certs_metadata_creates_rings(self):
        meta = ServiceProviderMetadataParser().parse(self.xml)
        provider = meta.to_provider("test-multi", self.flow, self.flow)

        self.assertEqual(provider.issuer, "https://sp-multi.example.org/shibboleth")
        self.assertEqual(provider.acs_url, "https://sp-multi.example.org/Shibboleth.sso/SAML2/POST")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)

        self.assertIsNone(provider.verification_kp)
        self.assertIsNotNone(provider.verification_kp_ring)
        self.assertIsNone(provider.encryption_kp)
        self.assertIsNotNone(provider.encryption_kp_ring)

        v = list(provider.verification_kp_ring.bindings.select_related("keypair").order_by("order"))
        self.assertEqual([b.order for b in v], [0, 1])
        self.assertTrue(all(b.keypair.certificate_data for b in v))

        e = list(provider.encryption_kp_ring.bindings.select_related("keypair").order_by("order"))
        self.assertEqual([b.order for b in e], [0, 1])
        self.assertTrue(all(b.keypair.certificate_data for b in e))

        self.assertIsNotNone(
            pick_cert_pem(kp=provider.verification_kp, ring=provider.verification_kp_ring)
        )

    def test_apply_to_provider_creates_and_syncs_keyrings(self):
        """apply_to_provider(create_missing_rings=True) creates rings and syncs certs."""
        meta = ServiceProviderMetadataParser().parse(self.xml)

        provider = SAMLProvider.objects.create(
            name="test-to-apply",
            authorization_flow=self.flow,
            invalidation_flow=self.flow,
            acs_url="https://dummy.invalid/acs",
            issuer="dummy",
            verification_kp=None,
            encryption_kp=None,
        )

        meta.apply_to_provider(provider, create_missing_rings=True)
        provider.refresh_from_db()

        self.assertIsNotNone(provider.verification_kp_ring)
        self.assertIsNotNone(provider.encryption_kp_ring)

        # ordering + count are the important bits (ring has what metadata had)
        v = list(provider.verification_kp_ring.bindings.order_by("order"))
        e = list(provider.encryption_kp_ring.bindings.order_by("order"))

        self.assertEqual(len(v), 2)
        self.assertEqual(len(e), 2)

        self.assertEqual([b.order for b in v], list(range(len(v))))
        self.assertEqual([b.order for b in e], list(range(len(e))))
