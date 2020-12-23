"""Test Service-Provider Metadata Parser"""

from authentik.providers.saml.models import SAMLBindings
from authentik.providers.saml.processors.metadata_parser import ServiceProviderMetadataParser
from django.test import TestCase

METADATA_SIMPLE = """<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     validUntil="2020-12-24T15:14:47Z"
                     cacheDuration="PT604800S"
                     entityID="http://localhost:8080/saml/metadata">
    <md:SPSSODescriptor AuthnRequestsSigned="false" WantAssertionsSigned="false" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified</md:NameIDFormat>
        <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                     Location="http://localhost:8080/saml/acs"
                                     index="1" />

    </md:SPSSODescriptor>
</md:EntityDescriptor>"""

class TestServiceProviderMetadataParser(TestCase):
    """Test ServiceProviderMetadataParser parsing and creation of SAML Provider"""

    def test_simple(self):
        """Test simple metadata without Singing"""
        metadata = ServiceProviderMetadataParser.parse(METADATA_SIMPLE)
        provider = metadata.to_provider("test")
        self.assertEqual(provider.acs_url, "http://localhost:8080/saml/acs")
        self.assertEqual(provider.issuer, "http://localhost:8080/saml/metadata")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
