"""Test Identity-Provider Metadata Parser"""

from base64 import b64encode

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate
from django.test import TestCase

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.lib.tests.utils import load_fixture
from authentik.sources.saml.models import SAMLNameIDPolicy
from authentik.sources.saml.processors.metadata_parser import IdentityProviderMetadataParser


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
