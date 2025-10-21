"""SAML Source tests"""

from base64 import b64encode

from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import dummy_get_response, load_fixture
from authentik.sources.saml.exceptions import InvalidEncryption, InvalidSignature
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.response import ResponseProcessor


class TestResponseProcessor(TestCase):
    """Test ResponseProcessor"""

    def setUp(self):
        self.factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer="authentik",
            allow_idp_initiated=True,
            pre_authentication_flow=create_test_flow(),
        )

    def test_status_error(self):
        """Test error status"""
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_error.xml").encode()
                ).decode()
            },
        )

        with self.assertRaisesMessage(
            ValueError,
            (
                "Invalid request, ACS Url in request http://localhost:9000/source/saml/google/acs/ "
                "doesn't match configured ACS Url https://127.0.0.1:9443/source/saml/google/acs/."
            ),
        ):
            ResponseProcessor(self.source, request).parse()

    def test_success(self):
        """Test success"""
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_success.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()
        self.assertEqual(
            sfm.user_properties,
            {
                "email": "foo@bar.baz",
                "name": "foo",
                "sn": "bar",
                "username": "jens@goauthentik.io",
                "attributes": {},
                "path": self.source.get_user_path(),
            },
        )

    def test_encrypted_correct(self):
        """Test encrypted"""
        key = load_fixture("fixtures/encrypted-key.pem")
        kp = CertificateKeyPair.objects.create(
            name=generate_id(),
            key_data=key,
        )
        self.source.encryption_kp = kp
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_encrypted.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()

    def test_encrypted_incorrect_key(self):
        """Test encrypted"""
        kp = create_test_cert()
        self.source.encryption_kp = kp
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_encrypted.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        with self.assertRaises(InvalidEncryption):
            parser.parse()

    def test_verification_assertion(self):
        """Test verifying signature inside assertion"""
        key = load_fixture("fixtures/signature_cert.pem")
        kp = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=key,
        )
        self.source.verification_kp = kp
        self.source.signed_assertion = True
        self.source.signed_response = False
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_signed_assertion.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()

    def test_verification_response(self):
        """Test verifying signature inside response"""
        key = load_fixture("fixtures/signature_cert.pem")
        kp = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=key,
        )
        self.source.verification_kp = kp
        self.source.signed_response = True
        self.source.signed_assertion = False
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_signed_response.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()

    def test_verification_response_and_assertion(self):
        """Test verifying signature inside response and assertion"""
        key = load_fixture("fixtures/signature_cert.pem")
        kp = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=key,
        )
        self.source.verification_kp = kp
        self.source.signed_assertion = True
        self.source.signed_response = True
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_signed_response_and_assertion.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()

    def test_verification_wrong_signature(self):
        """Test invalid signature fails"""
        key = load_fixture("fixtures/signature_cert.pem")
        kp = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=key,
        )
        self.source.verification_kp = kp
        self.source.signed_assertion = True
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    # Same as response_signed_assertion.xml but the role name is altered
                    load_fixture("fixtures/response_signed_error.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)

        with self.assertRaisesMessage(InvalidSignature, ""):
            parser.parse()

    def test_verification_no_signature(self):
        """Test rejecting response without signature when signed_assertion is True"""
        key = load_fixture("fixtures/signature_cert.pem")
        kp = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=key,
        )
        self.source.verification_kp = kp
        self.source.signed_assertion = True
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_success.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)

        with self.assertRaisesMessage(InvalidSignature, ""):
            parser.parse()

    def test_verification_incorrect_response(self):
        """Test verifying signature inside response"""
        key = load_fixture("fixtures/signature_cert.pem")
        kp = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=key,
        )
        self.source.verification_kp = kp
        self.source.signed_response = True
        self.source.signed_assertion = False
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_incorrect_signed_response.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        with self.assertRaisesMessage(InvalidSignature, ""):
            parser.parse()

    def test_signed_encrypted_response(self):
        """Test signed & encrypted response"""
        verification_key = load_fixture("fixtures/signature_cert2.pem")
        vkp = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=verification_key,
        )

        encrypted_key = load_fixture("fixtures/encrypted-key2.pem")
        ekp = CertificateKeyPair.objects.create(name=generate_id(), key_data=encrypted_key)

        self.source.verification_kp = vkp
        self.source.encryption_kp = ekp
        self.source.signed_response = True
        self.source.signed_assertion = False
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/test_signed_encrypted_response.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()
