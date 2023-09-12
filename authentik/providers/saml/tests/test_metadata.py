"""Test Service-Provider Metadata Parser"""
import xmlsec
from defusedxml.lxml import fromstring
from django.test import RequestFactory, TestCase
from lxml import etree  # nosec

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.lib.xml import lxml_from_string
from authentik.providers.saml.models import SAMLBindings, SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.providers.saml.processors.metadata_parser import ServiceProviderMetadataParser
from authentik.sources.saml.processors.constants import NS_MAP, NS_SAML_METADATA


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

        schema = etree.XMLSchema(etree.parse("schemas/saml-schema-metadata-2.0.xsd"))  # nosec
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
        provider = metadata.to_provider("test", self.flow)
        self.assertEqual(provider.acs_url, "http://localhost:8080/saml/acs")
        self.assertEqual(provider.issuer, "http://localhost:8080/saml/metadata")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(
            len(provider.property_mappings.all()),
            len(SAMLPropertyMapping.objects.exclude(managed__isnull=True)),
        )

    def test_with_signing_cert(self):
        """Test Metadata with signing cert"""
        create_test_cert()
        metadata = ServiceProviderMetadataParser().parse(load_fixture("fixtures/cert.xml"))
        provider = metadata.to_provider("test", self.flow)
        self.assertEqual(provider.acs_url, "http://localhost:8080/apps/user_saml/saml/acs")
        self.assertEqual(provider.issuer, "http://localhost:8080/apps/user_saml/saml/metadata")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(
            provider.verification_kp.certificate_data, load_fixture("fixtures/cert.pem")
        )
        self.assertIsNotNone(provider.signing_kp)
        self.assertEqual(provider.audience, "")

    def test_with_signing_cert_invalid_signature(self):
        """Test Metadata with signing cert (invalid signature)"""
        with self.assertRaises(ValueError):
            ServiceProviderMetadataParser().parse(
                load_fixture("fixtures/cert.xml").replace("/apps/user_saml", "")
            )

    def test_signature(self):
        """Test signature validation"""
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            signing_kp=create_test_cert(),
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
