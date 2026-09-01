"""Test password hash validators"""

from django.contrib.auth.hashers import (
    PBKDF2PasswordHasher,
    PBKDF2SHA1PasswordHasher,
    make_password,
)
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.lib.generators import generate_key
from authentik.lib.validators import (
    PasswordHashImportValidator,
    PasswordHashRequiresOverride,
    PasswordHashValidator,
)


class TestPasswordHashValidator(TestCase):
    """Test password hash validators."""

    def test_password_hash_validator(self):
        """Test password hash encoding validation."""
        password = generate_key()
        validator = PasswordHashValidator()
        validator(make_password(password))

        with self.assertRaises(ValidationError):
            validator("not-a-valid-hash")

    def test_password_hash_import_validator(self):
        """Test the password hash import policy."""
        password = generate_key()
        validator = PasswordHashImportValidator()
        validator(make_password(password))

        hasher = PBKDF2PasswordHasher()
        hasher.iterations -= 1
        stale = hasher.encode(password, hasher.salt())
        with self.assertRaises(PasswordHashRequiresOverride):
            validator(stale)

        sha1 = PBKDF2SHA1PasswordHasher()
        with self.assertRaises(PasswordHashRequiresOverride) as ctx:
            validator(sha1.encode(password, sha1.salt()))
        self.assertIn("pbkdf2_sha1", str(ctx.exception.detail[0]))

        hasher = PBKDF2PasswordHasher()
        hasher.iterations -= 1
        with self.assertRaises(PasswordHashRequiresOverride) as ctx:
            validator(hasher.encode(password, "salt"))
        self.assertEqual(len(ctx.exception.detail), 2)
        self.assertIn("Provided:", str(ctx.exception.detail[0]))
        self.assertIn(f"Iterations: {hasher.iterations}", str(ctx.exception.detail[0]))
        self.assertIn(
            f"Iterations: {PBKDF2PasswordHasher.iterations}", str(ctx.exception.detail[0])
        )
        self.assertNotIn("argon2", str(ctx.exception.detail[0]))
        self.assertIn("entropy", str(ctx.exception.detail[1]))
