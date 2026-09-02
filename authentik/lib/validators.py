"""Serializer validators"""

from typing import Any

from django.conf import settings
from django.contrib.auth.hashers import (
    BasePasswordHasher,
    identify_hasher,
    must_update_salt,
)
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer
from rest_framework.utils.representation import smart_repr

_PASSWORD_HASHER_PARAMETERS = (
    ("iterations", "iterations", _("Iterations")),
    ("work_factor", "rounds", _("Work factor")),
    ("time_cost", "time_cost", _("Time cost")),
    ("memory_cost", "memory_cost", _("Memory cost")),
    ("work_factor", "work_factor", _("Work factor")),
    ("block_size", "block_size", _("Block size")),
    ("parallelism", "parallelism", _("Parallelism")),
)


class PasswordHashRequiresOverride(ValidationError):
    """A valid password hash that does not match the current import policy."""


class PasswordHashValidator:
    """Validate the encoding of a Django password hash."""

    message = _(
        "Invalid password hash. The value must be a complete encoded password hash in one of "
        "authentik's configured formats."
    )

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
        messages: list[str] = []
        if hasher.algorithm not in settings.PASSWORD_HASH_IMPORT_ALLOWED_ALGORITHMS:
            messages.append(
                _(
                    "Password hash algorithm %(algorithm)s is not accepted. Accepted algorithms: "
                    "%(accepted_algorithms)s."
                )
                % {
                    "algorithm": hasher.algorithm,
                    "accepted_algorithms": ", ".join(
                        settings.PASSWORD_HASH_IMPORT_ALLOWED_ALGORITHMS
                    ),
                }
            )

        parameters = [
            (label, decoded[decoded_name], getattr(hasher, configured_name))
            for decoded_name, configured_name, label in _PASSWORD_HASHER_PARAMETERS
            if decoded_name in decoded and hasattr(hasher, configured_name)
        ]
        if any(provided != expected for _, provided, expected in parameters):
            messages.append(self._policy_message(hasher, parameters))

        if must_update_salt(decoded["salt"], hasher.salt_entropy):
            messages.append(
                _(
                    "Password hash salt does not meet the current requirement of "
                    "%(bits)d bits of entropy."
                )
                % {"bits": hasher.salt_entropy}
            )
        if messages:
            raise PasswordHashRequiresOverride(messages)

    def _policy_message(
        self,
        hasher: BasePasswordHasher,
        parameters: list[tuple[str, Any, Any]],
    ) -> str:
        """Describe the password hash parameters accepted for import."""
        provided = "\n".join(f"{label}: {value}" for label, value, _ in parameters)
        expected = "\n".join(f"{label}: {value}" for label, _, value in parameters)
        return _(
            "Password hash parameters do not match authentik's current policy.\n\n"
            "Provided:\nAlgorithm: %(algorithm)s\n%(provided)s\n\n"
            "Expected:\nAlgorithm: %(algorithm)s\n%(expected)s"
        ) % {
            "algorithm": hasher.algorithm,
            "provided": provided,
            "expected": expected,
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
