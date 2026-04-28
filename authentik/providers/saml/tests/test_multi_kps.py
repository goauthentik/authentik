"""Test multi-kp SAML KP support"""

from base64 import b64encode

from django.test import TestCase
from guardian.utils import get_anonymous_user

from authentik.core.tests.utils import RequestFactory, create_test_cert, create_test_flow
from authentik.crypto.models import (
    CertificateKeyPair,
    CertificateKeyPairRing,
    CertificateKeyPairRingBinding,
)
from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.authn_request_parser import AuthNRequestParser
from authentik.providers.saml.utils.keyring import candidate_cert_pems, pick_cert_pem
from authentik.sources.saml.models import SAMLBindingTypes, SAMLSource
from authentik.sources.saml.processors.request import RequestProcessor


class TestKeyringUtils(TestCase):
    def setUp(self) -> None:
        self.provider = SAMLProvider.objects.create(
            name="p1",
            authorization_flow=create_test_flow(),
            invalidation_flow=create_test_flow(),
            acs_url="https://sp.example.com/acs",
        )

        # create_test_cert() gives us a usable CertificateKeyPair (with PEM)
        self.kp1: CertificateKeyPair = create_test_cert()
        self.kp2: CertificateKeyPair = create_test_cert()

        # Make ordering visible (not required, but helps debugging)
        self.kp1.name = "kp1"
        self.kp1.save(update_fields=["name"])
        self.kp2.name = "kp2"
        self.kp2.save(update_fields=["name"])

        self.ring = CertificateKeyPairRing.objects.create(
            name="ring1",
        )

        # Put kp2 first, kp1 second (explicit ordering test)
        CertificateKeyPairRingBinding.objects.create(ring=self.ring, keypair=self.kp2, order=0)
        CertificateKeyPairRingBinding.objects.create(ring=self.ring, keypair=self.kp1, order=1)

        # Provider has both single KP and ring -> KP must win.
        self.provider.verification_kp = self.kp1
        self.provider.verification_kp_ring = self.ring
        self.provider.save()

    def test_candidate_cert_pems_prefers_single_kp_over_ring(self):
        pems = candidate_cert_pems(
            kp=self.provider.verification_kp, ring=self.provider.verification_kp_ring
        )
        self.assertEqual(pems, [(self.kp1.certificate_data or "").strip()])

    def test_candidate_cert_pems_uses_ring_order_when_no_single_kp(self):
        self.provider.verification_kp = None
        self.provider.save(update_fields=["verification_kp"])

        pems = candidate_cert_pems(kp=None, ring=self.provider.verification_kp_ring)
        self.assertEqual(
            pems,
            [
                (self.kp2.certificate_data or "").strip(),  # order=0
                (self.kp1.certificate_data or "").strip(),  # order=1
            ],
        )

    def test_pick_cert_pem_returns_first_candidate(self):
        self.provider.verification_kp = None
        self.provider.save(update_fields=["verification_kp"])

        pem = pick_cert_pem(kp=None, ring=self.provider.verification_kp_ring)
        self.assertEqual(pem, (self.kp2.certificate_data or "").strip())

    def test_candidate_cert_pems_empty_when_nothing_configured(self):
        self.provider.verification_kp = None
        self.provider.verification_kp_ring = None
        self.provider.save(update_fields=["verification_kp", "verification_kp_ring"])

        self.assertEqual(candidate_cert_pems(kp=None, ring=None), [])
        self.assertIsNone(pick_cert_pem(kp=None, ring=None))


class TestAuthNRequestMultiKey(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

        # Two different certs (different keypairs)
        self.kp1 = create_test_cert()
        self.kp2 = create_test_cert()

        # Provider (IdP side in authentik naming) - verification uses *ring only*
        self.provider = SAMLProvider.objects.create(
            name="p1",
            authorization_flow=create_test_flow(),
            invalidation_flow=create_test_flow(),
            acs_url="http://testserver/source/saml/provider/acs/",
        )

        self.ring = CertificateKeyPairRing.objects.create(
            name="p1-verification-ring",
        )
        # Put kp1 first, kp2 second (order shouldn't matter for success)
        CertificateKeyPairRingBinding.objects.create(ring=self.ring, keypair=self.kp1, order=0)
        CertificateKeyPairRingBinding.objects.create(ring=self.ring, keypair=self.kp2, order=1)

        self.provider.verification_kp = None
        self.provider.verification_kp_ring = self.ring
        self.provider.save()

        # Source (SP side in request direction) signs AuthnRequest with kp2
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            pre_authentication_flow=create_test_flow(),
            signing_kp=self.kp2,  # <-- this signs the AuthnRequest
            binding_type=SAMLBindingTypes.POST,
        )

    def test_parse_accepts_any_cert_in_verification_ring(self):
        """AuthNRequestParser should verify with any cert in verification_kp_ring."""
        http_request = self.request_factory.get("/", user=get_anonymous_user())

        req_proc = RequestProcessor(self.source, http_request, "test_state")
        xml = req_proc.build_auth_n()

        parsed = AuthNRequestParser(self.provider).parse(
            b64encode(xml.encode()).decode(),
            "test_state",
        )
        self.assertEqual(parsed.id, req_proc.request_id)
        self.assertEqual(parsed.relay_state, "test_state")

    def test_parse_fails_when_ring_does_not_contain_signing_cert(self):
        """If the ring doesn't include the signing cert, signature verification must fail."""
        # Replace ring content with kp1 only (remove kp2)
        CertificateKeyPairRingBinding.objects.filter(ring=self.ring).delete()
        CertificateKeyPairRingBinding.objects.create(ring=self.ring, keypair=self.kp1, order=0)

        http_request = self.request_factory.get("/", user=get_anonymous_user())
        req_proc = RequestProcessor(self.source, http_request, "test_state")
        xml = req_proc.build_auth_n()

        with self.assertRaises(CannotHandleAssertion):
            AuthNRequestParser(self.provider).parse(
                b64encode(xml.encode()).decode(),
                "test_state",
            )
