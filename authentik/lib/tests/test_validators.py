"""Test password hash validators"""

from django.contrib.auth.hashers import (
    PBKDF2PasswordHasher,
    PBKDF2SHA1PasswordHasher,
    make_password,
)
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.lib.generators import generate_key
from authentik.lib.validators import PasswordHashRequiresOverride, validate_password_hash


class TestValidatePasswordHash(TestCase):
    """Test validate_password_hash"""

    def test_validate_password_hash(self):
        """Test encoding and current-hasher policy."""
        password = generate_key()
        validate_password_hash(make_password(password), require_current=True)

        with self.assertRaises(ValidationError):
            validate_password_hash("not-a-valid-hash")

        hasher = PBKDF2PasswordHasher()
        hasher.iterations -= 1
        stale = hasher.encode(password, hasher.salt())
        validate_password_hash(stale)
        with self.assertRaises(PasswordHashRequiresOverride):
            validate_password_hash(stale, require_current=True)

        sha1 = PBKDF2SHA1PasswordHasher()
        with self.assertRaises(PasswordHashRequiresOverride):
            validate_password_hash(sha1.encode(password, sha1.salt()), require_current=True)

        with self.assertRaises(PasswordHashRequiresOverride) as ctx:
            validate_password_hash(
                PBKDF2PasswordHasher().encode(password, "salt"),
                require_current=True,
            )
        self.assertIn("entropy", str(ctx.exception.messages[0]))
