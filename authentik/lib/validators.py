"""Serializer validators"""

from base64 import b64decode
from typing import Any

from django.conf import settings
from django.contrib.auth.hashers import (
    Argon2PasswordHasher,
    BasePasswordHasher,
    BCryptSHA256PasswordHasher,
    PBKDF2PasswordHasher,
    ScryptPasswordHasher,
    identify_hasher,
    must_update_salt,
)
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer
from rest_framework.utils.representation import smart_repr

INVALID_PASSWORD_HASH_MESSAGE = _("Invalid password hash encoding.")

SUPPORTED_PASSWORD_HASHERS = tuple(
    import_string(password_hasher) for password_hasher in settings.PASSWORD_HASHERS
)
BCRYPT_ALPHABET = frozenset("./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
BCRYPT_SALT_LENGTH = 22
BCRYPT_CHECKSUM_LENGTH = 31


class PasswordHashRequiresOverride(ValueError):
    """An imported password hash does not match the default security policy."""


def _decode_base64(value: str, expected_length: int) -> None:
    """Decode a base64 value and verify its expected byte length."""
    decoded = b64decode(value + "=" * (-len(value) % 4), validate=True)
    if len(decoded) != expected_length:
        raise ValueError


def _decode_password_hash(
    password_hash: str,
) -> tuple[BasePasswordHasher, dict[str, Any]]:
    """Decode a password hash and validate the encoded digest structure."""
    hasher = identify_hasher(password_hash)
    decoded = hasher.decode(password_hash)

    if type(hasher) is PBKDF2PasswordHasher:
        _decode_base64(decoded["hash"], 32)
    elif type(hasher) is ScryptPasswordHasher:
        _decode_base64(decoded["hash"], 64)
    elif type(hasher) is Argon2PasswordHasher:
        _, _, _, _, salt, digest = password_hash.split("$")
        _decode_base64(salt, len(decoded["salt"]))
        _decode_base64(digest, decoded["params"].hash_len)
    elif type(hasher) is BCryptSHA256PasswordHasher:
        if (
            decoded["algostr"] != "2b"
            or len(decoded["salt"]) != BCRYPT_SALT_LENGTH
            or len(decoded["checksum"]) != BCRYPT_CHECKSUM_LENGTH
            or not set(decoded["salt"] + decoded["checksum"]).issubset(BCRYPT_ALPHABET)
        ):
            raise ValueError

    return hasher, decoded


def validate_password_hash(password_hash: str, *, require_current: bool = False) -> None:
    """Validate an encoded Django password and, optionally, its security parameters."""
    try:
        hasher, decoded = _decode_password_hash(password_hash)
    except (AssertionError, TypeError, ValueError) as exc:
        raise ValidationError(INVALID_PASSWORD_HASH_MESSAGE) from exc

    if require_current and (
        type(hasher) not in SUPPORTED_PASSWORD_HASHERS
        or hasher.must_update(password_hash)
        or must_update_salt(decoded["salt"], hasher.salt_entropy)
    ):
        raise PasswordHashRequiresOverride(
            _("Password hash does not meet authentik's current password hashing policy.")
        )


class RequiredTogetherValidator:
    """Serializer-level validator that ensures all fields in `fields` are only
    used together"""

    fields: list[str]
    requires_context = True
    message = _("The fields {field_names} must be used together.")

    def __init__(self, fields: list[str], message: str | None = None) -> None:
        self.fields = fields
        self.message = message or self.message

    def __call__(self, attrs: dict, serializer: Serializer):
        """Check that if any of the fields in `self.fields` are set, all of them must be set"""
        if any(field in attrs for field in self.fields) and not all(
            field in attrs for field in self.fields
        ):
            field_names = ", ".join(self.fields)
            message = self.message.format(field_names=field_names)
            raise ValidationError(message, code="required")

    def __repr__(self):
        return f"<{self.__class__.__name__}(fields={smart_repr(self.fields)})>"
