"""FIPS mode tests"""

import hashlib
from unittest import skipUnless

from cryptography.exceptions import InternalError, UnsupportedAlgorithm
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from django.test import SimpleTestCase


@skipUnless(backend._fips_enabled, "FIPS mode is off")
class TestFIPS(SimpleTestCase):
    """FIPS mode refuses algorithms that no FIPS standard approves. Ed25519 and ML-DSA aren't
    checked: they're approved, the current FIPS provider just doesn't have them."""

    def test_hashlib_md5(self):
        """MD5 for security use"""
        with self.assertRaises(ValueError):
            hashlib.md5(b"")  # nosec

    def test_hashlib_new(self):
        """hashlib.new() falls back to Python's builtin MD5, so these have no builtin"""
        for name in ("ripemd160", "sm3", "md5-sha1"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                hashlib.new(name, b"")

    def test_hashlib_pbkdf2_md5(self):
        """PBKDF2 with MD5"""
        with self.assertRaises(ValueError):
            hashlib.pbkdf2_hmac("md5", b"", b"salt", 1)

    def test_hashlib_scrypt(self):
        """scrypt"""
        with self.assertRaises(ValueError):
            hashlib.scrypt(b"", salt=b"salt", n=2, r=1, p=1)

    def test_cryptography_md5(self):
        """MD5, which only fails once OpenSSL initializes the digest"""
        with self.assertRaises((InternalError, UnsupportedAlgorithm)):
            hashes.Hash(hashes.MD5())  # nosec

    def test_cryptography_hmac_md5(self):
        """HMAC with MD5"""
        with self.assertRaises(UnsupportedAlgorithm):
            hmac.HMAC(b"key", hashes.MD5())  # nosec

    def test_cryptography_scrypt(self):
        """scrypt"""
        with self.assertRaises(UnsupportedAlgorithm):
            Scrypt(salt=b"salt", length=32, n=2, r=1, p=1).derive(b"")

    def test_cryptography_chacha20_poly1305(self):
        """ChaCha20-Poly1305"""
        with self.assertRaises(UnsupportedAlgorithm):
            ChaCha20Poly1305(b"k" * 32).encrypt(b"n" * 12, b"", None)
