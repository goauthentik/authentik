"""SAML Source tests"""

from base64 import b64encode  # noqa: I001

from django.test import TestCase
from freezegun import freeze_time

from authentik.core.models import SourceUserMatchingModes
from authentik.core.sources.matcher import Action, SourceMatcher
from authentik.core.tests.utils import (
    RequestFactory,
    create_test_cert,
    create_test_flow,
    create_test_user,
)
from authentik.crypto.models import CertificateKeyPairRing, CertificateKeyPairRingBinding
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.sources.saml.exceptions import InvalidEncryption, InvalidSignature
from authentik.sources.saml.models import (
    GroupSAMLSourceConnection,
    SAMLSource,
    UserSAMLSourceConnection,
)
from authentik.sources.saml.processors.response import ResponseProcessor

def _ring_add_keypairs(*, ring: CertificateKeyPairRing, keypairs: list[CertificateKeyPair]) -> None:
    for i, kp in enumerate(keypairs):
        CertificateKeyPairRingBinding.objects.create(ring=ring, keypair=kp, order=i)

class TestResponseProcessor(TestCase):
    """Test ResponseProcessor"""

    def setUp(self):
        self.factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer_override="authentik",
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

    @freeze_time("2022-10-14T14:15:00")
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

    @freeze_time("2022-10-14T14:16:40Z")
    def test_success_with_status_message_and_detail(self):
        """Test success with StatusMessage and StatusDetail present (should not raise error)"""
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_success_with_message.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()
        self.assertEqual(sfm.user_properties["username"], "jens@goauthentik.io")

    @freeze_time("2022-10-14T14:16:40Z")
    def test_error_with_message_and_detail(self):
        """Test error status with StatusMessage and StatusDetail includes both in error"""
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_error_with_detail.xml").encode()
                ).decode()
            },
        )

        with self.assertRaises(ValueError) as ctx:
            ResponseProcessor(self.source, request).parse()
        # Should contain both detail and message
        self.assertIn("User account is disabled", str(ctx.exception))
        self.assertIn("Authentication failed", str(ctx.exception))

    @freeze_time("2024-08-07T15:48:09.325Z")
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

    @freeze_time("2022-10-14T14:16:40Z")
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

    @freeze_time("2014-07-17T01:02:18Z")
    def test_verification_assertion_duplicate(self):
        """Test verifying signature inside assertion, where the response has another assertion
        before our signed assertion"""
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
                    load_fixture("fixtures/response_signed_assertion_dup.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        self.assertNotEqual(parser._get_name_id()[1], "bad")
        self.assertEqual(parser._get_name_id()[1], "_ce3d2948b4cf20146dee0a0b3dd6f69b6cf86f62d7")

    @freeze_time("2014-07-17T01:02:18Z")
    def test_verification_assertion_xsw_nested_duplicate_id(self):
        """Nested-duplicate-ID XSW: a forged outer Assertion shares its ID with a
        nested copy of the original signed Assertion (placed inside <saml:Advice>),
        so the Signature's Reference URI (#ORIG_ID) matches the outer Assertion's
        ID *and* dereferences to legitimately-signed content. Must be rejected."""
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
                    load_fixture("fixtures/response_signed_assertion_xsw_nested.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        with self.assertRaises(InvalidSignature):
            parser.parse()

    @freeze_time("2014-07-17T01:02:18Z")
    def test_verification_response_uri_empty(self):
        """Some real-world IdPs (notably some Okta dev-tenant configurations
        observed in the gosaml2 testdata corpus at saml.oktadev.com) sign the
        Response with ds:Reference URI="" instead of URI="#<ID>". Per xmldsig
        §4.4.3.2, URI="" covers the entire enclosing document via the
        enveloped-signature transform — strictly more attested content than
        "#<ID>" — so consuming the target is a subset of what was signed."""
        key = load_fixture("fixtures/signature_cert_uri_empty.pem")
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
                    load_fixture("fixtures/response_signed_response_uri_empty.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()

    @freeze_time("2014-07-17T01:02:18Z")
    def test_verification_assertion_uri_empty(self):
        """Symmetric to test_verification_response_uri_empty but for an
        Assertion-level signature: the same xmldsig "this document" semantics
        still cover the whole enclosing document, so the Assertion we then
        consume is part of the attested content. We have no real-world IdP
        samples emitting this configuration, but the pre-fix code accepted it
        and the cryptographic guarantee holds, so keep accepting it rather
        than risk breaking an IdP we haven't sampled."""
        key = load_fixture("fixtures/signature_cert_assertion_uri_empty.pem")
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
                    load_fixture("fixtures/response_signed_assertion_uri_empty.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()

    @freeze_time("2014-07-17T01:02:18Z")
    def test_verification_assertion_xsw3(self):
        """XSW-3 (signature relocation): a forged Assertion contains a Signature whose
        ds:Reference URI points to a second Assertion in the document. The signature
        verifies (because the digest matches the legitimate referenced Assertion),
        but the verifier must NOT then consume the forged Assertion as if it were
        signed."""
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
                    load_fixture("fixtures/response_signed_assertion_xsw3.xml").encode()
                ).decode()
            },
        )

        parser = ResponseProcessor(self.source, request)
        with self.assertRaises(InvalidSignature):
            parser.parse()

    @freeze_time("2014-07-17T01:02:18Z")
    def test_name_id_comment(self):
        """Test comment in name ID"""
        fixture = load_fixture("fixtures/response_signed_assertion.xml")
        fixture = fixture.replace(
            "_ce3d2948b4cf20146dee0a0b3dd6f69b6cf86f62d7",
            "_ce3d2948b4cf20146dee0a0b3dd6f<!--x-->69b6cf86f62d7",
        )
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
            data={"SAMLResponse": b64encode(fixture.encode()).decode()},
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        self.assertEqual(parser._get_name_id()[1], "_ce3d2948b4cf20146dee0a0b3dd6f69b6cf86f62d7")

    @freeze_time("2014-07-17T01:02:18Z")
    def test_name_id_comment_username_truncation(self):
        """Test that a comment in the NameID does not truncate the matching username.

        The connection identifier reads the full text content with
        ``"".join(name_id.itertext())``, so the username used for matching must read
        the same value and not ``name_id.text``, which returns only the text before
        the first child node."""
        full_name_id = "_ce3d2948b4cf20146dee0a0b3dd6f69b6cf86f62d7"
        # The text before the comment, which is what ``name_id.text`` returns.
        truncated_name_id = "_ce3d2948b4cf20146dee0a0b3dd6f"
        commented_name_id = f"{truncated_name_id}<!--x-->{full_name_id[len(truncated_name_id):]}"
        fixture = load_fixture("fixtures/response_signed_assertion.xml").replace(
            full_name_id, commented_name_id
        )
        key = load_fixture("fixtures/signature_cert.pem")
        kp = CertificateKeyPair.objects.create(name=generate_id(), certificate_data=key)
        self.source.verification_kp = kp
        self.source.signed_assertion = True
        self.source.signed_response = False
        self.source.user_matching_mode = SourceUserMatchingModes.USERNAME_LINK
        request = self.factory.post(
            "/",
            data={"SAMLResponse": b64encode(fixture.encode()).decode()},
        )

        parser = ResponseProcessor(self.source, request)
        # The comment is dropped by the signature canonicalization, so the signature
        # still verifies.
        parser.parse()

        name_id_el, identifier = parser._get_name_id()
        self.assertEqual(identifier, full_name_id)

        properties = self.source.get_base_user_properties(
            root=parser._root, assertion=parser.get_assertion(), name_id=name_id_el
        )
        # The username must match the full identifier, not the truncated text.
        self.assertEqual(properties["username"], identifier)

        # An existing user matching only the truncated text must not be linked.
        other_user = create_test_user(name=truncated_name_id)
        matcher = SourceMatcher(self.source, UserSAMLSourceConnection, GroupSAMLSourceConnection)
        action, connection = matcher.get_user_action(identifier, properties)
        self.assertEqual(action, Action.ENROLL)
        self.assertNotEqual(connection.user_id, other_user.pk)

    @freeze_time("2014-07-17T01:02:18Z")
    def test_attribute_value_comment_truncation(self):
        """Test that a comment in an attribute value does not truncate it.

        Attribute values feed user matching and property mappings, so a value must
        be read with ``"".join(value.itertext())`` and not ``value.text``, which
        returns only the text before the first child node."""
        fixture = load_fixture("fixtures/response_signed_assertion.xml").replace(
            "test@example.com", "test@<!--x-->example.com"
        )
        key = load_fixture("fixtures/signature_cert.pem")
        kp = CertificateKeyPair.objects.create(name=generate_id(), certificate_data=key)
        self.source.verification_kp = kp
        self.source.signed_assertion = True
        self.source.signed_response = False
        request = self.factory.post(
            "/",
            data={"SAMLResponse": b64encode(fixture.encode()).decode()},
        )

        parser = ResponseProcessor(self.source, request)
        parser.parse()

        name_id_el, _ = parser._get_name_id()
        properties = self.source.get_base_user_properties(
            root=parser._root, assertion=parser.get_assertion(), name_id=name_id_el
        )
        # The attribute value must not be truncated at the comment.
        self.assertEqual(properties["mail"], "test@example.com")

    @freeze_time("2014-07-17T01:02:18Z")
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

    @freeze_time("2024-01-18T06:20:48Z")
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

    @freeze_time("2022-10-14T14:15:00")
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

    @freeze_time("2025-10-30T05:45:47.619Z")
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

    @freeze_time("2026-01-21T14:23")
    def test_transient(self):
        """Test SAML transient NameID"""
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
        parser.prepare_flow_manager()

    def test_verification_assertion_with_ring(self):
        """Test verifying signature inside assertion via verification_kp_ring."""
        cert_pem = load_fixture("fixtures/signature_cert.pem")

        ring = CertificateKeyPairRing.objects.create(name=generate_id())
        ring.sync_membership([(0, cert_pem)])

        self.source.verification_kp = None
        self.source.verification_kp_ring = ring
        self.source.signed_assertion = True
        self.source.signed_response = False
        self.source.save()

        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_signed_assertion.xml").encode()
                ).decode()
            },
        )

        ResponseProcessor(self.source, request).parse()

    def test_verification_response_with_ring(self):
        """Test verifying signature inside response via verification_kp_ring."""
        cert_pem = load_fixture("fixtures/signature_cert.pem")

        ring = CertificateKeyPairRing.objects.create(name=generate_id())
        ring.sync_membership([(0, cert_pem)])

        self.source.verification_kp = None
        self.source.verification_kp_ring = ring
        self.source.signed_response = True
        self.source.signed_assertion = False
        self.source.save()

        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_signed_response.xml").encode()
                ).decode()
            },
        )

        ResponseProcessor(self.source, request).parse()

    def test_verification_ring_try_order(self):
        """Ring should try certs in order until one verifies."""
        good = load_fixture("fixtures/signature_cert.pem")
        bad = create_test_cert().certificate_data  # wrong cert

        ring = CertificateKeyPairRing.objects.create(name=generate_id())
        ring.sync_membership([(0, bad), (1, good)])

        self.source.verification_kp = None
        self.source.verification_kp_ring = ring
        self.source.signed_assertion = True
        self.source.signed_response = False
        self.source.save()

        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_signed_assertion.xml").encode()
                ).decode()
            },
        )

        ResponseProcessor(self.source, request).parse()

    def test_encrypted_correct_with_ring(self):
        """Decrypt using encryption_kp_ring (no encryption_kp)."""
        key_pem = load_fixture("fixtures/encrypted-key.pem")
        kp = CertificateKeyPair.objects.create(
            name=generate_id(),
            key_data=key_pem,
        )

        ring = CertificateKeyPairRing.objects.create(name=generate_id())
        _ring_add_keypairs(ring=ring, keypairs=[kp])

        self.source.encryption_kp = None
        self.source.encryption_kp_ring = ring
        self.source.save()

        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_encrypted.xml").encode()
                ).decode()
            },
        )

        ResponseProcessor(self.source, request).parse()

    def test_encrypted_ring_try_order(self):
        """Ring should try private keys in order until one decrypts."""
        bad = create_test_cert()  # has a private key but wrong one for this fixture
        good = CertificateKeyPair.objects.create(
            name=generate_id(),
            key_data=load_fixture("fixtures/encrypted-key.pem"),
        )

        ring = CertificateKeyPairRing.objects.create(name=generate_id())
        _ring_add_keypairs(ring=ring, keypairs=[bad, good])

        self.source.encryption_kp = None
        self.source.encryption_kp_ring = ring
        self.source.save()

        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_encrypted.xml").encode()
                ).decode()
            },
        )

        ResponseProcessor(self.source, request).parse()
