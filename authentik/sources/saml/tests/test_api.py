"""SAML Source API tests"""

from tempfile import TemporaryFile
from unittest import skipIf

from cryptography.hazmat.backends.openssl.backend import backend
from django.urls import reverse
from lxml import etree  # nosec
from rest_framework.test import APITestCase

from authentik.common.saml.constants import NS_MAP
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.lib.xml import lxml_from_string
from authentik.sources.saml.models import SAMLNameIDPolicy, SAMLSource

SIGNING_KEY_DESCRIPTORS = "//md:IDPSSODescriptor/md:KeyDescriptor[@use='signing']"


def cert_body(certificate: str) -> str:
    """A certificate's base64 body, without PEM armour or whitespace"""
    return "".join(part for part in certificate.split() if "-----" not in part)


def signing_cert_bodies(metadata: str) -> list[str]:
    """The IdP signing certificates listed in `metadata`, in order"""
    return [
        cert_body(text)
        for text in lxml_from_string(metadata.encode()).xpath(
            f"{SIGNING_KEY_DESCRIPTORS}//ds:X509Certificate/text()", namespaces=NS_MAP
        )
    ]


def without_first_signing_cert(metadata: str) -> str:
    """`metadata` after the IdP finished its rollover and dropped its first signing certificate"""
    root = lxml_from_string(metadata.encode())
    old = root.xpath(SIGNING_KEY_DESCRIPTORS, namespaces=NS_MAP)[0]
    old.getparent().remove(old)
    return etree.tostring(root).decode()


IDP_METADATA_XML = """<?xml version="1.0" encoding="UTF-8"?>
<EntityDescriptor
    xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
    entityID="https://idp.example.org/idp/shibboleth">
    <IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <KeyDescriptor use="signing">
            <ds:KeyInfo>
                <ds:X509Data>
                    <ds:X509Certificate>
MIIEJzCCAo+gAwIBAgIUA1yeQ2nU+Hxd20Ebmbwtdrv2bR4wDQYJKoZIhvcNAQEL
BQAwGjEYMBYGA1UEAwwPaWRwLmV4YW1wbGUub3JnMB4XDTI1MTAwODA4MjAzOFoX
DTQ1MTAwODA4MjAzOFowGjEYMBYGA1UEAwwPaWRwLmV4YW1wbGUub3JnMIIBojAN
BgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAq3c/HqS7172tqRznTaYrF9gJIETQ
FqTsUsWIBp6uc1RM6nj9NfpCJYS4/ic0/xjPvUDbeYczXYwyecIwzUS3YmSoezE5
Rw/lE+NtOn+PbGOXIBQ7EMSLBm2alYPz9FDYZze4fQ0gJKdTNouFV/iievgcbrW3
4tGUd5ckanZHLuNRn70r9dKzUBIqEf8eaDJF+8pMGbD7YFtrVj7Fu0dR305xJqXN
KkOEF+VILclzaa9SHMHoH2g5NiNTY8PH+/YV6+8VQa1f/IwoWMM+OsLxx/H6DqMs
A4EkNY14Xk/cpu0QFwJcQkyEsIxBqKrNfe/1Kgaggw5aANsjLfdcTMM3GTyyFTd8
Zxa9cjC0jWslMxRJ8g6T+nnKk7ZfbPwCWiHrRCXuqmRVjpdP9rPa2msJQ/Plwmrg
F9Yti/bQmJ+JypD2dqjCGgxhQNHNPxU8axGXVaDG6KXOBGkq79z2AXnFR66e380N
vgImlxmokp6MW/3/g01fZruCKwkepgEMhhzZAgMBAAGjZTBjMB0GA1UdDgQWBBTf
5ASoGUClCdq3rzS/3anEVKSdcjBCBgNVHREEOzA5gg9pZHAuZXhhbXBsZS5vcmeG
Jmh0dHBzOi8vaWRwLmV4YW1wbGUub3JnL2lkcC9zaGliYm9sZXRoMA0GCSqGSIb3
DQEBCwUAA4IBgQA9CKN0w437FVdwPJLv9qTshFxMY3RQf9+PkH41Fqd99tnM5yV/
LH1ieO7vY1MEWVEz3Zu+UDQPhX4Xslg2z08iSxY+VNv0ggJNrbUO4lYKhXc58UKg
Kq4gqcNi5Xx/y+LvpT5Wcm/Ps1hxcT7k55xOfY5W8VosMphV6G/Gl4sAY3zwoOBV
Y9RVg/75eyv/nGfGVV9DlxKvspds30eZfYUZ301XhDCbXhIhSveK+vxSfEyKOBhR
yFbFs2VrUSfC2spzUFqYGYIhFMajIp8VJ1of2HQUNZNK4Td/cOeQ3CL2Drr0VnpN
6nGNsKfP1it/p2VZ6MOpsgaFwXcvd+/eoY5PQE0UYLCUOXOsTHSeTg6dqrRhx+NN
5p4j1IcyMUbl31SC9xMWgLlM5YQNiC5G/CFZwIFxCLRY+WXSSzbbIteBkRJu5oOf
UEZRMegY+j3HrKlxLOrMMvNLL2h+kQAi/t454VzGeth3mmmhEMGP/LJVUDVBLk7l
hXXBo4Lf7ivi33g=
                    </ds:X509Certificate>
                </ds:X509Data>
            </ds:KeyInfo>
        </KeyDescriptor>
        <SingleSignOnService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            Location="https://idp.example.org/idp/profile/SAML2/Redirect/SSO"/>
        <SingleLogoutService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            Location="https://idp.example.org/idp/profile/SAML2/Redirect/SLO"/>
        <NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:persistent</NameIDFormat>
    </IDPSSODescriptor>
</EntityDescriptor>
"""


class TestSAMLSourceMetadataAPI(APITestCase):
    """SAML Source metadata import API tests"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_detail(self):
        source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer_override="authentik",
            sso_url="https://idp.example.org/sso",
            pre_authentication_flow=create_test_flow(),
        )
        response = self.client.get(
            reverse("authentik_api:samlsource-detail", kwargs={"slug": source.slug}),
        )
        self.assertEqual(200, response.status_code)

    def test_metadata(self):
        source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer_override="authentik",
            sso_url="https://idp.example.org/sso",
            pre_authentication_flow=create_test_flow(),
        )
        response = self.client.get(
            reverse("authentik_api:samlsource-metadata", kwargs={"slug": source.slug}),
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("metadata", response.json())

    def test_import_success(self):
        name = generate_id()
        pre_authentication_flow = create_test_flow()

        with TemporaryFile() as metadata:
            metadata.write(IDP_METADATA_XML.encode())
            metadata.seek(0)
            response = self.client.post(
                reverse("authentik_api:samlsource-import-metadata"),
                {
                    "file": metadata,
                    "name": name,
                    "pre_authentication_flow": pre_authentication_flow.pk,
                },
                format="multipart",
            )
        self.assertEqual(201, response.status_code)
        body = response.json()
        self.assertEqual(body["name"], name)
        self.assertEqual(body["pre_authentication_flow"], str(pre_authentication_flow.pk))

        source = SAMLSource.objects.get(slug=body["slug"])
        self.assertEqual(source.sso_url, "https://idp.example.org/idp/profile/SAML2/Redirect/SSO")
        self.assertEqual(source.slo_url, "https://idp.example.org/idp/profile/SAML2/Redirect/SLO")

    def _import_metadata(self, metadata: str, **data):
        with TemporaryFile() as file:
            file.write(metadata.encode())
            file.seek(0)
            return self.client.post(
                reverse("authentik_api:samlsource-import-metadata"),
                {"file": file, **data},
                format="multipart",
            )

    def test_import_multi_cert_creates_keyring(self):
        """Test the back- and front-channel signing certificates of a Shibboleth IdP are both
        trusted, in metadata order"""
        metadata = load_fixture("fixtures/idp-metadata.xml")
        response = self._import_metadata(
            metadata, name=generate_id(), pre_authentication_flow=create_test_flow().pk
        )
        self.assertEqual(response.status_code, 201)
        source = SAMLSource.objects.get(slug=response.json()["slug"])

        self.assertIsNone(source.verification_kp)
        bindings = list(source.verification_kp_ring.ordered_bindings())
        self.assertEqual([binding.order for binding in bindings], [0, 1])
        self.assertEqual(
            [cert_body(binding.keypair.certificate_data) for binding in bindings],
            signing_cert_bodies(metadata),
        )
        # The IdP's encryption certificate is of no use to a source
        self.assertIsNone(source.encryption_kp_ring)

    def test_import_existing_source_after_rollover(self):
        """Test re-importing metadata without the old certificate leaves only the new one"""
        metadata = load_fixture("fixtures/idp-metadata.xml")
        response = self._import_metadata(
            metadata, name=generate_id(), pre_authentication_flow=create_test_flow().pk
        )
        source = SAMLSource.objects.get(slug=response.json()["slug"])
        ring = source.verification_kp_ring

        response = self._import_metadata(
            without_first_signing_cert(metadata), source=source.pk, name=source.name
        )
        self.assertEqual(response.status_code, 200)
        source.refresh_from_db()

        self.assertEqual(source.verification_kp_ring, ring)
        bindings = list(source.verification_kp_ring.ordered_bindings())
        self.assertEqual(
            [cert_body(binding.keypair.certificate_data) for binding in bindings],
            signing_cert_bodies(metadata)[1:],
        )

    def test_import_failed_invalid_xml(self):
        with TemporaryFile() as metadata:
            metadata.write(b"invalid")
            metadata.seek(0)
            response = self.client.post(
                reverse("authentik_api:samlsource-import-metadata"),
                {
                    "file": metadata,
                    "name": generate_id(),
                    "pre_authentication_flow": create_test_flow().pk,
                },
                format="multipart",
            )
        self.assertEqual(400, response.status_code)


class TestSAMLSourceAPI(APITestCase):
    """SAML Source API tests"""

    def setUp(self) -> None:
        super().setUp()
        self.client.force_login(create_test_admin_user())

    @skipIf(backend._fips_enabled, "The FIPS provider has no Ed25519")
    def test_create_validate_unsupported_key_type(self):
        """Test validation rejects key types without an XML-DSIG transform (Ed25519)"""
        ed25519_cert = create_test_cert(PrivateKeyAlg.ED25519)

        response = self.client.post(
            reverse("authentik_api:samlsource-list"),
            data={
                "name": generate_id(),
                "slug": generate_id(),
                "sso_url": "http://localhost",
                "pre_authentication_flow": create_test_flow().pk,
                "signing_kp": ed25519_cert.pk,
                "verification_kp": ed25519_cert.pk,
                "encryption_kp": ed25519_cert.pk,
                "signed_assertion": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        message = (
            "Key type Ed25519 is not supported. Supported key types are: RSA, Elliptic Curve, DSA."
        )
        self.assertJSONEqual(
            response.content,
            {
                "signing_kp": [message],
                "verification_kp": [message],
                "encryption_kp": [message],
            },
        )

    def test_create_supported_key_type(self):
        """Test an RSA keypair is accepted on every keypair field"""
        cert = create_test_cert()

        response = self.client.post(
            reverse("authentik_api:samlsource-list"),
            data={
                "name": generate_id(),
                "slug": generate_id(),
                "sso_url": "http://localhost",
                "pre_authentication_flow": create_test_flow().pk,
                "signing_kp": cert.pk,
                "verification_kp": cert.pk,
                "encryption_kp": cert.pk,
                "signed_assertion": True,
            },
        )
        self.assertEqual(response.status_code, 201)
