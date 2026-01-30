"""SAML Source tests"""

from base64 import b64encode
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from authentik.core.models import SourceUserMatchingModes
from authentik.core.tests.utils import RequestFactory, create_test_cert, create_test_flow
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
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
                    load_fixture("fixtures/response_signed_encrypted.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()

    @patch("authentik.sources.saml.processors.response.now")
    def test_transient(self, mocked_now):
        """Test SAML transient NameID"""
        fixed_time = timezone.make_aware(timezone.datetime(2020, 10, 30, 19, 30))
        mocked_now.return_value = fixed_time
        verification_key = load_fixture("fixtures/signature_cert2.pem")
        vkp = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=verification_key,
        )
        self.source.verification_kp = vkp
        self.source.signed_response = True
        self.source.signed_assertion = False
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_transient.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()

        self.assertEqual(sfm.identifier, "test001@example.org")
        self.assertEqual(
            sfm.user_properties,
            {
                "username": "test001@example.org",
                "path": self.source.get_user_path(),
                "attributes": {},
                "email": "test001@mail.example.org",
                "eppn": "test001@example.org",
                "uid": "test001",
                "urn:oid:1.3.6.1.4.1.25178.1.2.9": "example.org",
            },
        )

    @patch("authentik.sources.saml.processors.response.now")
    def test_transient_simple(self, mocked_now):
        """Test SAML transient NameID without attributes"""
        mocked_now.return_value = timezone.make_aware(timezone.datetime(2020, 10, 30, 19, 30))
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_transient_simple.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()

        username = "_ef5783d83c0d4147212322815d7e4064"
        self.assertEqual(
            sfm.identifier,
            username,
        )
        self.assertEqual(
            sfm.user_properties,
            {
                "username": username,
                "path": self.source.get_user_path(),
                "urn:oid:1.3.6.1.4.1.25178.1.2.9": "example.org",
                "attributes": {
                    "goauthentik.io/user/delete-on-logout": True,
                    "goauthentik.io/user/expires": 1604172600.0,
                    "goauthentik.io/user/generated": True,
                    "goauthentik.io/user/sources": [self.source.name],
                },
            },
        )

    def test_persistent(self):
        """Test SAML persistent NameID"""
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_persistent.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()
        self.assertEqual(
            sfm.user_properties,
            {
                "email": "test001@example.org",
                "eppn": "test001@example.org",
                "urn:oid:1.3.6.1.4.1.25178.1.2.9": "example.org",
                "uid": "test001",
                "username": "LHPJHTQTRBOHWQRFZIYHL7PASE67UJVM",
                "path": self.source.get_user_path(),
                "attributes": {},
            },
        )

    def test_persistent_match_email(self):
        """Test SAML persistent NameID witch email matching"""
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_persistent.xml").encode()
                ).decode()
            },
        )

        self.source.user_matching_mode = SourceUserMatchingModes.EMAIL_LINK
        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()
        self.assertEqual(
            sfm.user_properties,
            {
                "eppn": "test001@example.org",
                "uid": "test001",
                "urn:oid:1.3.6.1.4.1.25178.1.2.9": "example.org",
                "email": "test001@example.org",
                "username": "LHPJHTQTRBOHWQRFZIYHL7PASE67UJVM",
                "path": self.source.get_user_path(),
                "attributes": {},
            },
        )

    def test_persistent_match_eppn(self):
        """Test SAML persistent NameID witch eppn matching"""
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_persistent.xml").encode()
                ).decode()
            },
        )

        self.source.user_matching_mode = SourceUserMatchingModes.USERNAME_LINK
        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()
        self.assertEqual(sfm.identifier, "LHPJHTQTRBOHWQRFZIYHL7PASE67UJVM")
        self.assertEqual(
            sfm.user_properties,
            {
                "uid": "test001",
                "email": "test001@example.org",
                "urn:oid:1.3.6.1.4.1.25178.1.2.9": "example.org",
                "eppn": "test001@example.org",
                "username": "test001@example.org",
                "path": self.source.get_user_path(),
                "attributes": {},
            },
        )
