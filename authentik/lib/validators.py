"""Serializer validators"""

from typing import Any

from django.contrib.auth.hashers import (
    BasePasswordHasher,
    get_hashers,
    identify_hasher,
    must_update_salt,
)
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer
from rest_framework.utils.representation import smart_repr


class PasswordHashRequiresOverride(Exception):
    """A valid password hash that does not match the current import policy."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__(" ".join(str(message) for message in messages))


class PasswordHashValidator:
    """Validate the encoding of a Django password hash."""

    message = _("Invalid password hash encoding.")

    def __call__(self, password_hash: str) -> None:
        self._decode(password_hash)

    def _decode(self, password_hash: str) -> tuple[BasePasswordHasher, dict[str, Any]]:
        """Return the hasher and decoded password hash."""
        try:
            hasher = identify_hasher(password_hash)
            return hasher, hasher.decode(password_hash)
        except (AssertionError, TypeError, ValueError) as exc:
            raise ValidationError(self.message) from exc


class PasswordHashImportValidator(PasswordHashValidator):
    """Validate a password hash against authentik's import policy."""

    def __call__(self, password_hash: str) -> None:
        hasher, decoded = self._decode(password_hash)
        importable = [
            configured_hasher
            for configured_hasher in get_hashers()
            if configured_hasher.algorithm != "pbkdf2_sha1"
        ]
        messages: list[str] = []
        salt_stale = must_update_salt(decoded["salt"], hasher.salt_entropy)
        # hasher.must_update() is also true for a short salt.
        if hasher not in importable or (hasher.must_update(password_hash) and not salt_stale):
            messages.append(self._policy_message(importable))
        if salt_stale:
            messages.append(
                _(
                    "Password hash salt does not meet the current requirement of "
                    "%(bits)d bits of entropy."
                )
                % {"bits": hasher.salt_entropy}
            )
        if messages:
            raise PasswordHashRequiresOverride(messages)

    def _policy_message(self, hashers: list[BasePasswordHasher]) -> str:
        """Describe the password hash parameters accepted for import."""
        expected: list[str] = []
        for hasher in hashers:
            params = ", ".join(
                f"{attr}={getattr(hasher, attr)}"
                for attr in (
                    "iterations",
                    "rounds",
                    "time_cost",
                    "memory_cost",
                    "work_factor",
                    "block_size",
                    "parallelism",
                )
                if hasattr(hasher, attr)
            )
            expected.append(f"{hasher.algorithm} ({params})")
        return _("Password hash parameters must match: %(expected)s.") % {
            "expected": "; ".join(expected)
        }


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
