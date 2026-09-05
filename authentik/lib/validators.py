"""Serializer validators"""

from typing import Any

from django.conf import settings
from django.contrib.auth.hashers import (
    BasePasswordHasher,
    identify_hasher,
    must_update_salt,
)
from django.utils.module_loading import import_string
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
    """A valid password hash that does not match the current import defaults."""


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
    """Validate a password hash against authentik's import settings."""

    def __call__(self, password_hash: str) -> None:
        hasher, decoded = self._decode(password_hash)
        messages = self._algorithm_messages(hasher)
        messages.extend(self._update_messages(password_hash, hasher, decoded))
        if messages:
            raise PasswordHashRequiresOverride(messages)

    def _algorithm_messages(self, hasher: BasePasswordHasher) -> list[str]:
        """Describe an algorithm that is not accepted for import."""
        allowed_algorithms = [
            import_string(path)().algorithm for path in settings.PASSWORD_HASHERS_IMPORT_ALLOWED
        ]
        if hasher.algorithm in allowed_algorithms:
            return []
        return [
            _(
                "Password hash algorithm %(algorithm)s is not accepted. Accepted algorithms: "
                "%(accepted_algorithms)s."
            )
            % {
                "algorithm": hasher.algorithm,
                "accepted_algorithms": ", ".join(allowed_algorithms),
            }
        ]

    def _update_messages(
        self,
        password_hash: str,
        hasher: BasePasswordHasher,
        decoded: dict[str, Any],
    ) -> list[str]:
        """Describe why Django requires an update to the password hash."""
        messages: list[str] = []
        parameters = self._parameters(hasher, decoded)
        requires_update = hasher.must_update(password_hash)
        if requires_update and any(provided != expected for _, provided, expected in parameters):
            messages.append(self._settings_message(hasher, parameters))

        salt_needs_update = must_update_salt(decoded["salt"], hasher.salt_entropy)
        if salt_needs_update:
            messages.append(
                _(
                    "Password hash salt does not meet the current requirement of "
                    "%(bits)d bits of entropy."
                )
                % {"bits": hasher.salt_entropy}
            )

        # must_update() remains authoritative when the displayed fields do not expose its reason.
        if requires_update and not messages:
            messages.append(self._settings_message(hasher, parameters))
        return messages

    def _parameters(
        self,
        hasher: BasePasswordHasher,
        decoded: dict[str, Any],
    ) -> list[tuple[str, Any, Any]]:
        """Return password hash parameters for the error message."""
        parameters = [
            (label, decoded[decoded_name], getattr(hasher, configured_name))
            for decoded_name, configured_name, label in _PASSWORD_HASHER_PARAMETERS
            if decoded_name in decoded and hasattr(hasher, configured_name)
        ]
        if "params" in decoded:
            expected = hasher.params()
            parameters.extend(
                (
                    (_("Variety"), decoded["variety"], f"argon2{expected.type.name.lower()}"),
                    (_("Version"), decoded["version"], expected.version),
                    (_("Hash length"), decoded["params"].hash_len, expected.hash_len),
                )
            )
        return parameters

    def _settings_message(
        self,
        hasher: BasePasswordHasher,
        parameters: list[tuple[str, Any, Any]],
    ) -> str:
        """Describe the password hash parameters accepted for import."""
        provided = "\n".join(f"{label}: {value}" for label, value, _ in parameters)
        expected = "\n".join(f"{label}: {value}" for label, _, value in parameters)
        return _(
            "Password hash parameters do not match authentik's current settings for algorithm "
            "%(algorithm)s.\n\nProvided:\n%(provided)s\n\nExpected:\n%(expected)s"
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
