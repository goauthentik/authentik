"""Test password hash validators"""

from argon2.low_level import Type, hash_secret
from django.contrib.auth.hashers import (
    Argon2PasswordHasher,
    PBKDF2PasswordHasher,
    PBKDF2SHA1PasswordHasher,
    check_password,
)
from django.test import TestCase

from authentik.lib.generators import generate_key
from authentik.lib.validators import (
    PasswordHashImportValidator,
    PasswordHashRequiresOverride,
)


class TestPasswordHashImportValidator(TestCase):
    """Test password hash import settings."""

    def test_rejected_algorithm_lists_allowed_algorithms(self):
        """The algorithm error lists every accepted algorithm."""
        password = generate_key()
        validator = PasswordHashImportValidator()

        sha1 = PBKDF2SHA1PasswordHasher()
        with self.assertRaises(PasswordHashRequiresOverride) as ctx:
            validator(sha1.encode(password, sha1.salt()))
        algorithm_error = str(ctx.exception.detail[0])
        self.assertIn("pbkdf2_sha1", algorithm_error)
        self.assertIn("pbkdf2_sha256, argon2, bcrypt_sha256, scrypt", algorithm_error)

    def test_argon2i_requires_override(self):
        """Django's must_update flags an otherwise current argon2i hash."""
        password = generate_key()
        validator = PasswordHashImportValidator()
        argon2 = Argon2PasswordHasher()
        params = argon2.params()
        argon2i = (
            argon2.algorithm
            + hash_secret(
                password.encode(),
                argon2.salt().encode(),
                time_cost=params.time_cost,
                memory_cost=params.memory_cost,
                parallelism=params.parallelism,
                hash_len=params.hash_len,
                type=Type.I,
            ).decode()
        )
        self.assertTrue(check_password(password, argon2i))
        with self.assertRaises(PasswordHashRequiresOverride) as ctx:
            validator(argon2i)
        self.assertIn("Variety: argon2i", str(ctx.exception.detail[0]))
        self.assertIn("Variety: argon2id", str(ctx.exception.detail[0]))

    def test_parameters_and_salt_have_separate_errors(self):
        """Parameter and salt mismatches are reported separately."""
        password = generate_key()
        validator = PasswordHashImportValidator()
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
