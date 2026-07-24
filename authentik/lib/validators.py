"""Serializer validators"""

from base64 import b64decode
from typing import Any

from django.contrib.auth.hashers import (
    Argon2PasswordHasher,
    BasePasswordHasher,
    BCryptSHA256PasswordHasher,
    PBKDF2PasswordHasher,
    PBKDF2SHA1PasswordHasher,
    ScryptPasswordHasher,
    identify_hasher,
    must_update_salt,
)
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer
from rest_framework.utils.representation import smart_repr

INVALID_PASSWORD_HASH_MESSAGE = _("Invalid password hash encoding.")

BCRYPT_ALPHABET = frozenset("./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
BCRYPT_SALT_LENGTH = 22
BCRYPT_CHECKSUM_LENGTH = 31


class PasswordHashRequiresOverride(ValueError):
    """An imported password hash does not match the default security policy."""

    messages: list[str]

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__(" ".join(str(message) for message in messages))


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
    elif type(hasher) is PBKDF2SHA1PasswordHasher:
        _decode_base64(decoded["hash"], 20)
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

    if not require_current:
        return

    messages: list[str] = []
    # Keep this handling in sync with the hashers configured in settings.PASSWORD_HASHERS.
    if type(hasher) in (PBKDF2PasswordHasher, PBKDF2SHA1PasswordHasher):
        if decoded["iterations"] != hasher.iterations:
            messages.append(
                _("%(algorithm)s hashes must use %(iterations)d iterations.")
                % {"algorithm": hasher.algorithm, "iterations": hasher.iterations}
            )
    elif type(hasher) is BCryptSHA256PasswordHasher:
        if decoded["work_factor"] != hasher.rounds:
            messages.append(
                _("bcrypt_sha256 hashes must use a work factor of %(work_factor)d.")
                % {"work_factor": hasher.rounds}
            )
    elif type(hasher) is ScryptPasswordHasher:
        if (
            decoded["work_factor"] != hasher.work_factor
            or decoded["block_size"] != hasher.block_size
            or decoded["parallelism"] != hasher.parallelism
        ):
            messages.append(
                _(
                    "scrypt hashes must use work factor %(work_factor)d, block size "
                    "%(block_size)d, and parallelism %(parallelism)d."
                )
                % {
                    "work_factor": hasher.work_factor,
                    "block_size": hasher.block_size,
                    "parallelism": hasher.parallelism,
                }
            )
    elif type(hasher) is Argon2PasswordHasher:
        parameters = hasher.params()
        variant = f"argon2{parameters.type.name.lower()}"
        if (
            decoded["variety"] != variant
            or decoded["version"] != parameters.version
            or decoded["time_cost"] != parameters.time_cost
            or decoded["memory_cost"] != parameters.memory_cost
            or decoded["parallelism"] != parameters.parallelism
            or decoded["params"].hash_len != parameters.hash_len
        ):
            messages.append(
                _(
                    "argon2 hashes must use variant %(variant)s, version %(version)d, time cost "
                    "%(time_cost)d, memory cost %(memory_cost)d, parallelism %(parallelism)d, "
                    "and hash length %(hash_length)d."
                )
                % {
                    "variant": variant,
                    "version": parameters.version,
                    "time_cost": parameters.time_cost,
                    "memory_cost": parameters.memory_cost,
                    "parallelism": parameters.parallelism,
                    "hash_length": parameters.hash_len,
                }
            )
    if must_update_salt(decoded["salt"], hasher.salt_entropy):
        messages.append(
            _(
                "Password hash salt does not meet authentik's current requirement of "
                "%(expected_entropy)d bits of entropy. Importing it can enable timing-based "
                "user enumeration."
            )
            % {"expected_entropy": hasher.salt_entropy}
        )
    if messages:
        raise PasswordHashRequiresOverride(messages)


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
