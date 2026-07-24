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


def _password_hash_parameters(
    hasher: BasePasswordHasher, decoded: dict[str, Any]
) -> dict[str, tuple[str | int, str | int]]:
    """Return the provided and current work parameters for a password hasher."""
    # Keep this handling in sync with the hashers configured in settings.PASSWORD_HASHERS.
    parameters: dict[str, tuple[str | int, str | int]] = {
        str(_("Algorithm")): (decoded["algorithm"], hasher.algorithm),
    }

    if type(hasher) in (PBKDF2PasswordHasher, PBKDF2SHA1PasswordHasher):
        parameters[str(_("Iterations"))] = (decoded["iterations"], hasher.iterations)
    elif type(hasher) is BCryptSHA256PasswordHasher:
        parameters[str(_("Work factor"))] = (decoded["work_factor"], hasher.rounds)
    elif type(hasher) is ScryptPasswordHasher:
        parameters.update(
            {
                str(_("Work factor")): (decoded["work_factor"], hasher.work_factor),
                str(_("Block size")): (decoded["block_size"], hasher.block_size),
                str(_("Parallelism")): (decoded["parallelism"], hasher.parallelism),
            }
        )
    elif type(hasher) is Argon2PasswordHasher:
        expected = hasher.params()
        parameters.update(
            {
                str(_("Variant")): (
                    decoded["variety"],
                    f"argon2{expected.type.name.lower()}",
                ),
                str(_("Version")): (decoded["version"], expected.version),
                str(_("Time cost")): (decoded["time_cost"], expected.time_cost),
                str(_("Memory cost")): (decoded["memory_cost"], expected.memory_cost),
                str(_("Parallelism")): (decoded["parallelism"], expected.parallelism),
                str(_("Hash length")): (decoded["params"].hash_len, expected.hash_len),
            }
        )
    return parameters


def _format_password_hash_parameters(
    parameters: dict[str, tuple[str | int, str | int]], *, expected: bool
) -> str:
    """Format either the provided or current password hash parameters."""
    value_index = 1 if expected else 0
    return "; ".join(
        str(_("%(name)s: %(value)s") % {"name": name, "value": values[value_index]})
        for name, values in parameters.items()
    )


def validate_password_hash(password_hash: str, *, require_current: bool = False) -> None:
    """Validate an encoded Django password and, optionally, its security parameters."""
    try:
        hasher, decoded = _decode_password_hash(password_hash)
    except (AssertionError, TypeError, ValueError) as exc:
        raise ValidationError(INVALID_PASSWORD_HASH_MESSAGE) from exc

    if not require_current:
        return

    messages: list[str] = []
    parameters = _password_hash_parameters(hasher, decoded)
    if any(provided != expected for provided, expected in parameters.values()):
        messages.append(
            _(
                "Password hash parameters do not match authentik's current configuration. "
                "Provided: %(provided)s. Expected: %(expected)s. "
                "Importing it can weaken password security."
            )
            % {
                "provided": _format_password_hash_parameters(parameters, expected=False),
                "expected": _format_password_hash_parameters(parameters, expected=True),
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
