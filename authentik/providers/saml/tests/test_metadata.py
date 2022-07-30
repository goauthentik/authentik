"""Test Service-Provider Metadata Parser"""
# flake8: noqa

from django.test import RequestFactory, TestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.providers.saml.models import SAMLBindings, SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.providers.saml.processors.metadata_parser import ServiceProviderMetadataParser

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

METADATA_CERT = """<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" validUntil="2020-12-24T16:25:48Z" cacheDuration="PT604800S" entityID="http://localhost:8080/apps/user_saml/saml/metadata" ID="pfx67a2a913-dd26-d65e-64c2-503fcd5eea47"><ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <ds:SignedInfo><ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
    <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
  <ds:Reference URI="#pfx67a2a913-dd26-d65e-64c2-503fcd5eea47"><ds:Transforms><ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/><ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/></ds:Transforms><ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/><ds:DigestValue>dPEwDuMayrdAgjhYvtiy3GTcP0n+BDi3sX+aistTDac=</ds:DigestValue></ds:Reference></ds:SignedInfo><ds:SignatureValue>MMspOlqURPLT2ELAD5RRHw4mBIWBGWAEedwMM6Dh7kzhJE/1z+dNgobM8e1Lr9Ztd/ygW7oUfwfbUqS8OVCxdI+fJtzai0Jm08/rq8VpNEZqTfALNQqlGDD2Uma63/8iFycrhYkaY8feoyT0ZfHTNuMDxHjtl1l52+q+1mx6ax5w9z/WzuSKBTndg+Gjh0XTN0ynI136MgXrJg4dBFtkIKq9u6PlJW42C+uqAoRoi29Vil6mT/dgctS2ZB118nGFeryN4oi2zgM9lkmWW6E5YtPdQxggKJqR8Zl+XnyHt3nh1X7uWN+691lXO6LG1YXtagD/BSMeUnfMV/dLCptv3w==</ds:SignatureValue>
<ds:KeyInfo><ds:X509Data><ds:X509Certificate>MIIDBzCCAe+gAwIBAgIQR8PqIN59R5mRygzU9JfD2TANBgkqhkiG9w0BAQsFADArMSkwJwYDVQQDDCBwYXNzYm9vayBTZWxmLXNpZ25lZCBDZXJ0aWZpY2F0ZTAeFw0yMDA3MDUxMTEzMTRaFw0yMTA3MDYxMTEzMTRaMFQxKTAnBgNVBAMMIHBhc3Nib29rIFNlbGYtc2lnbmVkIENlcnRpZmljYXRlMREwDwYDVQQKDAhwYXNzYm9vazEUMBIGA1UECwwLU2VsZi1zaWduZWQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC89aKl+gUw7X0d25LY5PQ0DuOlrIQf1iaY/X4uM1FNAaMfAnd653EE+ugerZWvAtRGke2QElVgsvvGfMN6XfH/zSWxkklvXPsuM2HfW6Yv8FcaQRTB2jXBUzU6wNjwF8V8TdFPpbVzQxXOvJyP8Z2YhUNRjy0OQzTV5bD21b2fhpWcNCCSJxIeZQxKjwQNpt6xiGt0JXODgE8hp7psrKBMYa2O3MAmdCu1b0ixbfkam0Vm9vDHUyjRi2N9S7lkiIP2fYEDi0v0zRq9/yV/0MEel4towY+WcNnLvKTsww80vFrgUI4K0r4bS9uBWZaClvycE0ZSMYHZG6TZBCUtEd2JAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAFMbcuq8oL2tfvBFMktv722r2FbbRXs7ky4IE2m42eaGEuhgdmrLsHaH4m3X+1TZgCufMGgoF8iVKQmpeaPSCDPKGW+yue+HLqCk5PIeQISDrEUwWNLx8lza7tm9Xdr1B3Q8/jxv1qtokhzhaBkCvYy92gvIgio5QaFKaFOSIp2Crrhh+R+uvmtronKe8RPx6XEk4EaAvXAfgGUV+xoQ9b54mt8gBwmZuLz86vIQBFSjOmPXEWYHe3FXAsB6i5eJMXtdBF7C3VbL3wBqOqddBPQ6+ojY+cUmNqVYbtXmAcjIveoJDi8Rs4F5pmlhGahnMgW8mqYtbHlUY7ytSUTowXA=</ds:X509Certificate></ds:X509Data></ds:KeyInfo></ds:Signature>
  <md:SPSSODescriptor AuthnRequestsSigned="true" WantAssertionsSigned="true" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:KeyDescriptor use="signing">
      <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
        <ds:X509Data>
          <ds:X509Certificate>MIIDBzCCAe+gAwIBAgIQR8PqIN59R5mRygzU9JfD2TANBgkqhkiG9w0BAQsFADArMSkwJwYDVQQDDCBwYXNzYm9vayBTZWxmLXNpZ25lZCBDZXJ0aWZpY2F0ZTAeFw0yMDA3MDUxMTEzMTRaFw0yMTA3MDYxMTEzMTRaMFQxKTAnBgNVBAMMIHBhc3Nib29rIFNlbGYtc2lnbmVkIENlcnRpZmljYXRlMREwDwYDVQQKDAhwYXNzYm9vazEUMBIGA1UECwwLU2VsZi1zaWduZWQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC89aKl+gUw7X0d25LY5PQ0DuOlrIQf1iaY/X4uM1FNAaMfAnd653EE+ugerZWvAtRGke2QElVgsvvGfMN6XfH/zSWxkklvXPsuM2HfW6Yv8FcaQRTB2jXBUzU6wNjwF8V8TdFPpbVzQxXOvJyP8Z2YhUNRjy0OQzTV5bD21b2fhpWcNCCSJxIeZQxKjwQNpt6xiGt0JXODgE8hp7psrKBMYa2O3MAmdCu1b0ixbfkam0Vm9vDHUyjRi2N9S7lkiIP2fYEDi0v0zRq9/yV/0MEel4towY+WcNnLvKTsww80vFrgUI4K0r4bS9uBWZaClvycE0ZSMYHZG6TZBCUtEd2JAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAFMbcuq8oL2tfvBFMktv722r2FbbRXs7ky4IE2m42eaGEuhgdmrLsHaH4m3X+1TZgCufMGgoF8iVKQmpeaPSCDPKGW+yue+HLqCk5PIeQISDrEUwWNLx8lza7tm9Xdr1B3Q8/jxv1qtokhzhaBkCvYy92gvIgio5QaFKaFOSIp2Crrhh+R+uvmtronKe8RPx6XEk4EaAvXAfgGUV+xoQ9b54mt8gBwmZuLz86vIQBFSjOmPXEWYHe3FXAsB6i5eJMXtdBF7C3VbL3wBqOqddBPQ6+ojY+cUmNqVYbtXmAcjIveoJDi8Rs4F5pmlhGahnMgW8mqYtbHlUY7ytSUTowXA=</ds:X509Certificate>
        </ds:X509Data>
      </ds:KeyInfo>
    </md:KeyDescriptor>
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="http://localhost:8080/apps/user_saml/saml/acs" index="1"/>
  </md:SPSSODescriptor>
</md:EntityDescriptor>"""

CERT = """-----BEGIN CERTIFICATE-----
MIIDBzCCAe+gAwIBAgIQR8PqIN59R5mRygzU9JfD2TANBgkqhkiG9w0BAQsFADAr
MSkwJwYDVQQDDCBwYXNzYm9vayBTZWxmLXNpZ25lZCBDZXJ0aWZpY2F0ZTAeFw0y
MDA3MDUxMTEzMTRaFw0yMTA3MDYxMTEzMTRaMFQxKTAnBgNVBAMMIHBhc3Nib29r
IFNlbGYtc2lnbmVkIENlcnRpZmljYXRlMREwDwYDVQQKDAhwYXNzYm9vazEUMBIG
A1UECwwLU2VsZi1zaWduZWQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIB
AQC89aKl+gUw7X0d25LY5PQ0DuOlrIQf1iaY/X4uM1FNAaMfAnd653EE+ugerZWv
AtRGke2QElVgsvvGfMN6XfH/zSWxkklvXPsuM2HfW6Yv8FcaQRTB2jXBUzU6wNjw
F8V8TdFPpbVzQxXOvJyP8Z2YhUNRjy0OQzTV5bD21b2fhpWcNCCSJxIeZQxKjwQN
pt6xiGt0JXODgE8hp7psrKBMYa2O3MAmdCu1b0ixbfkam0Vm9vDHUyjRi2N9S7lk
iIP2fYEDi0v0zRq9/yV/0MEel4towY+WcNnLvKTsww80vFrgUI4K0r4bS9uBWZaC
lvycE0ZSMYHZG6TZBCUtEd2JAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAFMbcuq8
oL2tfvBFMktv722r2FbbRXs7ky4IE2m42eaGEuhgdmrLsHaH4m3X+1TZgCufMGgo
F8iVKQmpeaPSCDPKGW+yue+HLqCk5PIeQISDrEUwWNLx8lza7tm9Xdr1B3Q8/jxv
1qtokhzhaBkCvYy92gvIgio5QaFKaFOSIp2Crrhh+R+uvmtronKe8RPx6XEk4EaA
vXAfgGUV+xoQ9b54mt8gBwmZuLz86vIQBFSjOmPXEWYHe3FXAsB6i5eJMXtdBF7C
3VbL3wBqOqddBPQ6+ojY+cUmNqVYbtXmAcjIveoJDi8Rs4F5pmlhGahnMgW8mqYt
bHlUY7ytSUTowXA=
-----END CERTIFICATE-----"""


class TestServiceProviderMetadataParser(TestCase):
    """Test ServiceProviderMetadataParser parsing and creation of SAML Provider"""

    def setUp(self) -> None:
        self.flow = create_test_flow()
        self.factory = RequestFactory()

    def test_consistent(self):
        """Test that metadata generation is consistent"""
        provider = SAMLProvider.objects.create(
            name="test",
            authorization_flow=self.flow,
        )
        Application.objects.create(
            name="test",
            slug="test",
            provider=provider,
        )
        request = self.factory.get("/")
        metadata_a = MetadataProcessor(provider, request).build_entity_descriptor()
        metadata_b = MetadataProcessor(provider, request).build_entity_descriptor()
        self.assertEqual(metadata_a, metadata_b)

    def test_simple(self):
        """Test simple metadata without Signing"""
        metadata = ServiceProviderMetadataParser().parse(METADATA_SIMPLE)
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
        metadata = ServiceProviderMetadataParser().parse(METADATA_CERT)
        provider = metadata.to_provider("test", self.flow)
        self.assertEqual(provider.acs_url, "http://localhost:8080/apps/user_saml/saml/acs")
        self.assertEqual(provider.issuer, "http://localhost:8080/apps/user_saml/saml/metadata")
        self.assertEqual(provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(provider.verification_kp.certificate_data, CERT)
        self.assertIsNotNone(provider.signing_kp)
        self.assertEqual(provider.audience, "")

    def test_with_signing_cert_invalid_signature(self):
        """Test Metadata with signing cert (invalid signature)"""
        with self.assertRaises(ValueError):
            ServiceProviderMetadataParser().parse(METADATA_CERT.replace("/apps/user_saml", ""))
