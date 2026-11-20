"""Test ECDH-ES key agreement for XML Encryption"""

from base64 import b64decode, b64encode
from os import urandom

import xmlsec
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.test import TestCase
from lxml import etree  # nosec

from authentik.common.saml.constants import NS_ENC, NS_SIGNATURE
from authentik.common.saml.key_agreement import (
    NS_MAP,
    build_encrypted_key,
    find_encrypted_key,
    unwrap_encrypted_key,
)
from authentik.core.tests.utils import create_test_cert
from authentik.crypto.builder import PrivateKeyAlg
from authentik.lib.tests.utils import load_fixture
from authentik.lib.xml import lxml_from_string
from authentik.sources.saml.exceptions import InvalidEncryption


class TestKeyAgreement(TestCase):
    """Test ECDH-ES key agreement for XML Encryption"""

    def load_vector(self, name: str) -> tuple[etree._Element, ec.EllipticCurvePrivateKey]:
        """Load a vector that was encrypted by xmlsec1 and the key it was encrypted for"""
        encrypted_data = lxml_from_string(load_fixture(f"fixtures/key_agreement_{name}.xml"))
        private_key = load_pem_private_key(
            load_fixture(f"fixtures/key_agreement_{name}.pem").encode(), None
        )
        return encrypted_data, private_key

    def test_unwrap_vectors(self):
        """Test decrypting data another implementation (xmlsec1) encrypted using ECDH-ES, which
        covers every curve, key wrap algorithm, key derivation digest and both ways of sending
        the originator key"""
        for name in ("p256", "p384", "p521"):
            with self.subTest(name=name):
                encrypted_data, private_key = self.load_vector(name)
                encrypted_key = find_encrypted_key(encrypted_data)
                self.assertIsNotNone(encrypted_key)

                encryption_context = xmlsec.EncryptionContext()
                encryption_context.key = xmlsec.Key.from_binary_data(
                    xmlsec.constants.KeyDataAes, unwrap_encrypted_key(encrypted_key, private_key)
                )
                # Decrypting an element replaces it in the tree, which needs a parent
                root = etree.Element("root")
                root.append(encrypted_data)
                decrypted = encryption_context.decrypt(encrypted_data)
                self.assertEqual(decrypted.tag, "{urn:goauthentik:test}secret")
                self.assertEqual(decrypted.text, f"authentik-{name}")

    def test_build_unwrap(self):
        """Test wrapping a key for a certificate and unwrapping it with its private key"""
        for curve in (ec.SECP256R1, ec.SECP384R1, ec.SECP521R1):
            for key_size in (16, 32):
                with self.subTest(curve=curve.name, key_size=key_size):
                    cert = create_test_cert(PrivateKeyAlg.ECDSA)
                    private_key = ec.generate_private_key(curve())
                    # Only the public key of the certificate is used
                    certificate = _CertificateStub(cert.certificate, private_key.public_key())
                    key = urandom(key_size)
                    encrypted_key = build_encrypted_key(certificate, key)
                    self.assertEqual(unwrap_encrypted_key(encrypted_key, private_key), key)
                    # A new ephemeral key is used every time
                    self.assertNotEqual(
                        etree.tostring(encrypted_key),
                        etree.tostring(build_encrypted_key(certificate, key)),
                    )

    def test_build_rsa(self):
        """Test that a key can't be wrapped for an RSA certificate using key agreement"""
        with self.assertRaises(InvalidEncryption):
            build_encrypted_key(create_test_cert().certificate, urandom(32))

    def test_find_encrypted_key(self):
        """Test that only encrypted keys using key agreement are found"""
        encrypted_data = etree.Element(f"{{{NS_ENC}}}EncryptedData")
        key_info = etree.SubElement(encrypted_data, f"{{{NS_SIGNATURE}}}KeyInfo")
        # Key transport, as used for RSA certificates
        etree.SubElement(key_info, f"{{{NS_ENC}}}EncryptedKey")
        self.assertIsNone(find_encrypted_key(encrypted_data))
        self.assertIsNotNone(find_encrypted_key(self.load_vector("p256")[0]))

    def test_unwrap_wrong_key(self):
        """Test unwrapping with a key the data wasn't encrypted for"""
        encrypted_data, private_key = self.load_vector("p256")
        encrypted_key = find_encrypted_key(encrypted_data)
        for name, key in (
            ("same curve", ec.generate_private_key(private_key.curve)),
            ("different curve", ec.generate_private_key(ec.SECP384R1())),
            ("rsa", create_test_cert().private_key),
        ):
            with self.subTest(name=name), self.assertRaises(InvalidEncryption):
                unwrap_encrypted_key(encrypted_key, key)

    def test_unwrap_tampered(self):
        """Test that modified or unsupported key agreement parameters are rejected"""

        def flip(node: etree._Element):
            raw = bytearray(b64decode(node.text))
            raw[-1] ^= 0x01
            node.text = b64encode(bytes(raw)).decode()

        def set_algorithm(node: etree._Element):
            node.attrib["Algorithm"] = "urn:unsupported"

        def remove(node: etree._Element):
            node.getparent().remove(node)

        def set_kdf_param(node: etree._Element):
            node.attrib["AlgorithmID"] = "00FF"

        def set_partial_octet(node: etree._Element):
            # A bitstring that isn't made of whole octets
            node.attrib["AlgorithmID"] = "0400"

        def set_not_hex(node: etree._Element):
            node.attrib["AlgorithmID"] = "zz"

        for name, xpath, mutate in (
            ("wrapped key", "xenc:CipherData/xenc:CipherValue", flip),
            ("no wrapped key", "xenc:CipherData/xenc:CipherValue", remove),
            ("originator key", ".//dsig11:PublicKey", flip),
            ("no originator key", ".//xenc:OriginatorKeyInfo", remove),
            ("originator curve", ".//dsig11:NamedCurve", remove),
            ("key wrap algorithm", "xenc:EncryptionMethod", set_algorithm),
            ("key agreement algorithm", ".//xenc:AgreementMethod", set_algorithm),
            ("key derivation algorithm", ".//xenc11:KeyDerivationMethod", set_algorithm),
            ("no key derivation", ".//xenc11:KeyDerivationMethod", remove),
            ("no key derivation params", ".//xenc11:ConcatKDFParams", remove),
            ("key derivation digest", ".//xenc11:ConcatKDFParams/ds:DigestMethod", set_algorithm),
            ("key derivation param", ".//xenc11:ConcatKDFParams", set_kdf_param),
            ("partial octet param", ".//xenc11:ConcatKDFParams", set_partial_octet),
            ("invalid param", ".//xenc11:ConcatKDFParams", set_not_hex),
        ):
            with self.subTest(name=name):
                encrypted_data, private_key = self.load_vector("p256")
                encrypted_key = find_encrypted_key(encrypted_data)
                mutate(encrypted_key.xpath(xpath, namespaces=NS_MAP)[0])
                with self.assertRaises(InvalidEncryption):
                    unwrap_encrypted_key(encrypted_key, private_key)

    def test_unwrap_originator_curve_mismatch(self):
        """Test that an originator key on a different curve than the decryption key is
        rejected"""
        encrypted_data, private_key = self.load_vector("p256")
        other_data, _ = self.load_vector("p521")
        encrypted_key = find_encrypted_key(encrypted_data)
        originator = encrypted_key.xpath(".//xenc:OriginatorKeyInfo", namespaces=NS_MAP)[0]
        originator.getparent().replace(
            originator, other_data.xpath(".//xenc:OriginatorKeyInfo", namespaces=NS_MAP)[0]
        )
        with self.assertRaises(InvalidEncryption):
            unwrap_encrypted_key(encrypted_key, private_key)


class _CertificateStub:
    """Certificate with a different public key, to wrap keys for curves that test certificates
    can't be generated with"""

    def __init__(self, certificate, public_key):
        self._certificate = certificate
        self._public_key = public_key

    def public_key(self):
        return self._public_key

    def public_bytes(self, encoding):
        return self._certificate.public_bytes(encoding)
