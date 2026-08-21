"""Serializer validators"""

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

INVALID_PASSWORD_HASH_MESSAGE = _("Invalid password hash encoding.")


class PasswordHashRequiresOverride(Exception):
    """A valid password hash that does not match the current import policy."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__(" ".join(str(message) for message in messages))


def _importable_hashers() -> list[BasePasswordHasher]:
    return [hasher for hasher in get_hashers() if hasher.algorithm != "pbkdf2_sha1"]


def _current_policy_message(hashers: list[BasePasswordHasher]) -> str:
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


def validate_password_hash(password_hash: str, *, require_current: bool = False) -> None:
    """Validate an encoded Django password, optionally against current hasher parameters."""
    try:
        hasher = identify_hasher(password_hash)
        decoded = hasher.decode(password_hash)
    except (AssertionError, TypeError, ValueError) as exc:
        raise ValidationError(INVALID_PASSWORD_HASH_MESSAGE) from exc

    if not require_current:
        return

    importable = _importable_hashers()
    messages: list[str] = []
    salt_stale = must_update_salt(decoded["salt"], hasher.salt_entropy)
    # hasher.must_update() is also true for a short salt.
    if hasher not in importable or (hasher.must_update(password_hash) and not salt_stale):
        messages.append(_current_policy_message(importable))
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
