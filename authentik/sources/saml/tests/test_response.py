"""SAML Source tests"""

from base64 import b64encode

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import dummy_get_response, load_fixture
from authentik.sources.saml.exceptions import InvalidEncryption
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

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

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

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

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

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

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

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

        parser = ResponseProcessor(self.source, request)
        with self.assertRaises(InvalidEncryption):
            parser.parse()
