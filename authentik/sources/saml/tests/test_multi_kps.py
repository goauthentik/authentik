from base64 import b64encode

from django.http.request import QueryDict
from django.test import TestCase
from guardian.utils import get_anonymous_user

from authentik.core.tests.utils import RequestFactory, create_test_cert, create_test_flow
from authentik.crypto.models import (
    CertificateKeyPair,
    CertificateKeyPairRing,
    CertificateKeyPairRingBinding,
)
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.authn_request_parser import AuthNRequestParser
from authentik.sources.saml.exceptions import InvalidEncryption, InvalidSignature
from authentik.sources.saml.models import SAMLBindingTypes, SAMLSource
from authentik.sources.saml.processors.request import RequestProcessor
from authentik.sources.saml.processors.response import ResponseProcessor


class TestSourceProcessorMultiKeyEndToEnd(TestCase):
    """No-fixture tests: generate signed/encrypted response via AssertionProcessor and parse via ResponseProcessor."""

    def setUp(self):
        self.request_factory = RequestFactory()

        # signing cert used by provider (IdP) to sign response/assertion
        self.kp_sign_good = create_test_cert()
        self.kp_sign_bad = create_test_cert()

        # encryption cert/key used by source (SP) to decrypt
        self.kp_enc_good = create_test_cert()
        self.kp_enc_bad = create_test_cert()

        # Provider (IdP side in authentik naming)
        self.provider = SAMLProvider.objects.create(
            name="p1",
            authorization_flow=create_test_flow(),
            invalidation_flow=create_test_flow(),
            acs_url="http://testserver/source/saml/provider/acs/",
            signing_kp=self.kp_sign_good,
            verification_kp=self.kp_sign_good,  # used to verify AuthnRequest (not the main topic here)
        )

        # Source (SP side in request direction)
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            pre_authentication_flow=create_test_flow(),
            signing_kp=create_test_cert(),  # request signing; not critical for these tests
            binding_type=SAMLBindingTypes.POST,
            allow_idp_initiated=True,
        )

    def _make_ring(self, name: str, keypairs: list[CertificateKeyPair]) -> CertificateKeyPairRing:
        ring = CertificateKeyPairRing.objects.create(name=name)
        for idx, kp in enumerate(keypairs):
            CertificateKeyPairRingBinding.objects.create(ring=ring, keypair=kp, order=idx)
        return ring

    def _build_response(self) -> str:
        """Build a SAMLResponse string from provider -> source, no fixtures."""
        http_request = self.request_factory.get("/", user=get_anonymous_user())

        # IdP-initiated request: avoids AuthnRequest signature verification entirely
        parsed_req = AuthNRequestParser(self.provider).idp_initiated()
        parsed_req.relay_state = "test_state"  # optional, if your AssertionProcessor uses it

        resp_proc = AssertionProcessor(self.provider, http_request, parsed_req)
        return resp_proc.build_response()

    def _parse_on_source(self, response_xml: str):
        """Parse the provider-generated response on the source ResponseProcessor."""
        http_request = self.request_factory.get("/", user=get_anonymous_user())
        http_request.POST = QueryDict(mutable=True)
        http_request.POST["SAMLResponse"] = b64encode(response_xml.encode()).decode()
        parser = ResponseProcessor(self.source, http_request)
        parser.parse()
        return parser

    def test_verify_response_signature_with_ring(self):
        """source.verification_kp_ring should accept the provider's signing cert (even if first cert is wrong)."""
        self.provider.sign_response = True
        self.provider.sign_assertion = False
        self.provider.save(update_fields=["sign_response", "sign_assertion"])

        # ring: wrong first, correct second -> must still verify
        self.source.verification_kp = None
        self.source.verification_kp_ring = self._make_ring(
            "verify-ring",
            [self.kp_sign_bad, self.kp_sign_good],
        )
        self.source.signed_response = True
        self.source.signed_assertion = False
        self.source.save(
            update_fields=[
                "verification_kp",
                "verification_kp_ring",
                "signed_response",
                "signed_assertion",
            ]
        )

        response_xml = self._build_response()
        self._parse_on_source(response_xml)

    def test_verify_response_signature_fails_if_ring_missing_cert(self):
        """If ring doesn't contain provider signing cert, verification must fail."""
        self.provider.sign_response = True
        self.provider.sign_assertion = False
        self.provider.save(update_fields=["sign_response", "sign_assertion"])

        self.source.verification_kp = None
        self.source.verification_kp_ring = self._make_ring(
            "verify-ring",
            [self.kp_sign_bad],
        )
        self.source.signed_response = True
        self.source.signed_assertion = False
        self.source.save(
            update_fields=[
                "verification_kp",
                "verification_kp_ring",
                "signed_response",
                "signed_assertion",
            ]
        )

        response_xml = self._build_response()
        with self.assertRaises(InvalidSignature):
            self._parse_on_source(response_xml)

    def test_decrypt_encrypted_assertion_with_ring(self):
        """source.encryption_kp_ring should decrypt even if first key is wrong (multi-private-key trial)."""
        # Provider encrypts assertion to SP public cert (certificate only is enough on provider)
        cert_only_for_provider = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=self.kp_enc_good.certificate_data,
            key_data="",  # IdP doesn't need SP private key
        )
        self.provider.encryption_kp = cert_only_for_provider
        self.provider.sign_response = False
        self.provider.sign_assertion = False
        self.provider.save(update_fields=["encryption_kp", "sign_response", "sign_assertion"])

        # Source decrypts with ring (wrong first, correct second)
        self.source.encryption_kp = None
        self.source.encryption_kp_ring = self._make_ring(
            "decrypt-ring",
            [self.kp_enc_bad, self.kp_enc_good],
        )
        self.source.save(update_fields=["encryption_kp", "encryption_kp_ring"])

        response_xml = self._build_response()
        self._parse_on_source(response_xml)

    def test_decrypt_fails_if_ring_missing_private_key(self):
        """If ring doesn't contain correct private key, decryption must fail."""
        cert_only_for_provider = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=self.kp_enc_good.certificate_data,
            key_data="",
        )
        self.provider.encryption_kp = cert_only_for_provider
        self.provider.save(update_fields=["encryption_kp"])

        self.source.encryption_kp = None
        self.source.encryption_kp_ring = self._make_ring(
            "decrypt-ring",
            [self.kp_enc_bad],
        )
        self.source.save(update_fields=["encryption_kp", "encryption_kp_ring"])

        response_xml = self._build_response()
        with self.assertRaises(InvalidEncryption):
            self._parse_on_source(response_xml)

    def test_verify_and_decrypt_with_rings(self):
        """Signed response + encrypted assertion: verification via ring, decryption via ring."""
        # sign response
        self.provider.sign_response = True
        self.provider.sign_assertion = False

        # encrypt to SP cert-only
        cert_only_for_provider = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=self.kp_enc_good.certificate_data,
            key_data="",
        )
        self.provider.encryption_kp = cert_only_for_provider
        self.provider.save(update_fields=["sign_response", "sign_assertion", "encryption_kp"])

        # source rings
        self.source.verification_kp = None
        self.source.verification_kp_ring = self._make_ring("verify-ring", [self.kp_sign_bad, self.kp_sign_good])
        self.source.signed_response = True
        self.source.signed_assertion = False

        self.source.encryption_kp = None
        self.source.encryption_kp_ring = self._make_ring("decrypt-ring", [self.kp_enc_bad, self.kp_enc_good])
        self.source.save(
            update_fields=[
                "verification_kp",
                "verification_kp_ring",
                "signed_response",
                "signed_assertion",
                "encryption_kp",
                "encryption_kp_ring",
            ]
        )

        response_xml = self._build_response()
        self._parse_on_source(response_xml)
