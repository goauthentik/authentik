"""Test password hashers"""

from bcrypt import gensalt, hashpw
from django.contrib.auth.hashers import check_password, identify_hasher
from django.test import TestCase

from authentik.lib.hashers import BCRYPT_MAX_PASSWORD_BYTES, BCryptPasswordHasher


class TestBCryptPasswordHasher(TestCase):
    """Test plain bcrypt hasher"""

    def _import(self, password: bytes) -> str:
        """Hash like other bcrypt implementations, which truncate to 72 bytes"""
        return f"bcrypt${hashpw(password[:BCRYPT_MAX_PASSWORD_BYTES], gensalt(4)).decode()}"

    def test_identified(self):
        """Test plain bcrypt hashes are identified by this hasher"""
        hasher = identify_hasher(self._import(b"password"))
        self.assertIsInstance(hasher, BCryptPasswordHasher)

    def test_verify(self):
        """Test correct and wrong passwords"""
        encoded = self._import(b"password")
        self.assertTrue(check_password("password", encoded))
        self.assertFalse(check_password("wrong", encoded))

    def test_verify_long_password(self):
        """Test passwords longer than 72 bytes verify like in the original application"""
        # "ä" is two bytes in UTF-8, so the 72 byte boundary splits a character
        password = "a" * 71 + "ä" * 10
        encoded = self._import(password.encode())
        self.assertTrue(check_password(password, encoded))
        self.assertFalse(check_password("b" * 100, encoded))
