"""SAML Source API Tests"""

from tempfile import TemporaryFile

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.sources.saml.models import SAMLNameIDPolicy, SAMLSource

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


class TestSAMLSourceAPI(APITestCase):
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
