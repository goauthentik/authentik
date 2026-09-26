"""Test Service-Provider Metadata Parser"""

from base64 import b64decode

import xmlsec
from cryptography.x509 import load_der_x509_certificate
from defusedxml.lxml import fromstring
from django.test import RequestFactory, TestCase
from lxml import etree  # nosec

from authentik.common.saml.constants import (
    AES128_CBC,
    AES256_GCM,
    ECDSA_SHA256,
    NS_MAP,
    NS_SAML_METADATA,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.lib.xml import lxml_from_string
from authentik.providers.saml.models import SAMLBindings, SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.providers.saml.processors.metadata_parser import ServiceProviderMetadataParser
from authentik.sources.saml.models import SAMLNameIDPolicy


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
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(provider.default_name_id_policy, SAMLNameIDPolicy.EMAIL)
        self.assertEqual(
            len(provider.property_mappings.all()),
            len(SAMLPropertyMapping.objects.exclude(managed__isnull=True)),
        )

    def test_encryption_algorithm_selection(self):
        """Test that the SP's advertised encryption algorithm preference is honored"""
        parser = ServiceProviderMetadataParser()

        def root_with_methods(*algorithms: str):
            methods = "".join(
                f'<md:EncryptionMethod Algorithm="{algorithm}"/>' for algorithm in algorithms
            )
            return lxml_from_string(
                (
                    '<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" '
                    'entityID="http://localhost:8080/saml/metadata">'
                    "<md:SPSSODescriptor protocolSupportEnumeration="
                    '"urn:oasis:names:tc:SAML:2.0:protocol">'
                    '<md:KeyDescriptor use="encryption">'
                    f"{methods}"
                    "</md:KeyDescriptor></md:SPSSODescriptor></md:EntityDescriptor>"
                ).encode()
            )

        # First supported algorithm in document order wins (honoring SP preference)
        self.assertEqual(
            parser.get_encryption_algorithm(root_with_methods(AES256_GCM, AES128_CBC)),
            AES256_GCM,
        )
        # Unsupported algorithms are skipped, next supported one is picked
        self.assertEqual(
            parser.get_encryption_algorithm(
                root_with_methods("http://www.w3.org/2001/04/xmlenc#tripledes-cbc", AES128_CBC)
            ),
            AES128_CBC,
        )
        # No supported algorithm advertised -> None (caller keeps the default)
        self.assertIsNone(
            parser.get_encryption_algorithm(
                root_with_methods("http://www.w3.org/2001/04/xmlenc#tripledes-cbc")
            )
        )
        # No EncryptionMethod advertised at all -> None
        self.assertIsNone(parser.get_encryption_algorithm(root_with_methods()))

    def test_encryption_algorithm_to_provider(self):
        """Test that a metadata-advertised encryption algorithm is applied to the provider"""
        cert_body = "".join(
            line
            for line in load_fixture("fixtures/cert.pem").splitlines()
            if "CERTIFICATE" not in line
        )
        metadata = (
            '<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" '
            'xmlns:ds="http://www.w3.org/2000/09/xmldsig#" '
            'entityID="http://localhost:8080/saml/metadata">'
            "<md:SPSSODescriptor protocolSupportEnumeration="
            '"urn:oasis:names:tc:SAML:2.0:protocol">'
            '<md:KeyDescriptor use="encryption">'
            f'<md:EncryptionMethod Algorithm="{AES256_GCM}"/>'
            f"<ds:KeyInfo><ds:X509Data><ds:X509Certificate>{cert_body}"
            "</ds:X509Certificate></ds:X509Data></ds:KeyInfo>"
            "</md:KeyDescriptor>"
            "<md:AssertionConsumerService "
            'Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" '
            'Location="http://localhost:8080/saml/acs" index="1"/>'
            "</md:SPSSODescriptor></md:EntityDescriptor>"
        )
        parsed = ServiceProviderMetadataParser().parse(metadata)
        self.assertEqual(parsed.encryption_algorithm, AES256_GCM)
        provider = parsed.to_provider("test", self.flow, self.flow)
        self.assertIsNotNone(provider.encryption_kp)
        self.assertEqual(provider.encryption_algorithm, AES256_GCM)

    def test_multiple_bindings(self):
        """Test metadata advertising endpoints with bindings authentik doesn't support"""
        metadata = ServiceProviderMetadataParser().parse(
            load_fixture("fixtures/multi_bindings.xml")
        )
        provider = metadata.to_provider("test", self.flow, self.flow)
        self.assertEqual(provider.acs_url, "https://sp-b.example.org/Shibboleth.sso/SAML2/POST")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(provider.sls_url, "https://sp-b.example.org/Shibboleth.sso/SLO/POST")
        self.assertEqual(provider.sls_binding, SAMLBindings.POST)
        self.assertEqual(provider.default_name_id_policy, SAMLNameIDPolicy.EMAIL)

    def test_multiple_bindings_default(self):
        """Test that an ACS marked as isDefault takes precedence over the order they're listed in"""
        metadata = ServiceProviderMetadataParser().parse(
            load_fixture("fixtures/multi_bindings.xml").replace(
                'bindings:HTTP-Artifact" '
                'Location="https://sp-b.example.org/Shibboleth.sso/SAML2/Artifact"',
                'bindings:HTTP-POST" '
                'Location="https://sp-b.example.org/Shibboleth.sso/SAML2/POST-Default" '
                'isDefault="true"',
            )
        )
        self.assertEqual(
            metadata.acs_location, "https://sp-b.example.org/Shibboleth.sso/SAML2/POST-Default"
        )
        self.assertEqual(metadata.acs_binding, SAMLBindings.POST)

    def test_no_supported_binding(self):
        """Test metadata with no ACS using a supported binding"""
        with self.assertRaises(ValueError):
            ServiceProviderMetadataParser().parse(
                load_fixture("fixtures/multi_bindings.xml").replace(
                    'bindings:HTTP-POST"', 'bindings:PAOS"'
                )
            )

    def test_with_signing_cert(self):
        """Test Metadata with signing cert"""
        create_test_cert()
        metadata = ServiceProviderMetadataParser().parse(load_fixture("fixtures/cert.xml"))
        provider = metadata.to_provider("test", self.flow, self.flow)
        self.assertEqual(provider.acs_url, "http://localhost:8080/apps/user_saml/saml/acs")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(
            provider.verification_kp.certificate_data, load_fixture("fixtures/cert.pem")
        )
        self.assertIsNotNone(provider.signing_kp)
        self.assertEqual(provider.audience, "http://localhost:8080/apps/user_saml/saml/metadata")

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

    def test_signing_kp_chain(self):
        """Test that only the leaf certificate of a certificate chain is included"""
        leaf = create_test_cert()
        intermediate = create_test_cert()
        leaf.certificate_data += intermediate.certificate_data
        leaf.save()
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            signing_kp=leaf,
        )
        Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=provider,
        )
        request = self.factory.get("/")
        metadata = lxml_from_string(MetadataProcessor(provider, request).build_entity_descriptor())

        certs = metadata.xpath(
            "/md:EntityDescriptor/md:IDPSSODescriptor/md:KeyDescriptor[@use='signing']"
            "/ds:KeyInfo/ds:X509Data/ds:X509Certificate",
            namespaces=NS_MAP,
        )
        self.assertEqual(len(certs), 1)
        self.assertEqual(
            load_der_x509_certificate(b64decode(certs[0].text, validate=True)),
            leaf.certificate,
        )

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

    def test_doctype(self):
        """Test that metadata with a document type declaration is refused"""
        metadata = load_fixture("fixtures/simple.xml").replace(
            '<?xml version="1.0"?>',
            '<?xml version="1.0"?><!DOCTYPE md:EntityDescriptor>',
        )

        with self.assertRaisesMessage(ValueError, "XML document contains a DOCTYPE declaration"):
            ServiceProviderMetadataParser().parse(metadata)
