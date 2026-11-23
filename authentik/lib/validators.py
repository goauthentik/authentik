"""Serializer validators"""

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


class PasswordHashRequiresOverride(ValidationError):
    """A valid password hash that does not match the current import defaults."""


class PasswordHashValidator:
    """Validate a Django password hash."""

    def __init__(self, strict: bool = True):
        self.strict = strict

    def __call__(self, password_hash: str) -> None:
        # 1. Validate hash function
        allowed_algorithms = [
            import_string(path)().algorithm for path in settings.PASSWORD_HASHERS_IMPORT_ALLOWED
        ]
        try:
            hasher = identify_hasher(password_hash)
        except ValueError as exc:
            raise ValidationError(
                "Cannot identify hash function. "
                f"Password hash must use one of: {", ".join(allowed_algorithms)}."
            ) from exc
        if self.strict and hasher.algorithm not in allowed_algorithms:
            raise PasswordHashRequiresOverride(
                f"Hash function {hasher.algorithm} not allowed. "
                f"Password hash must use one of: {", ".join(allowed_algorithms)}."
            )

        # 2. Validate hash
        try:
            decoded = hasher.decode(password_hash)
        # `AssertionError` is here because Django is stupid. "default$1$2$3" triggers it.
        except (AssertionError, ValueError) as exc:
            raise ValidationError("Password hash could not be decoded.") from exc

        if not self.strict:
            return
        # Django decides whether the hash needs an update, we only explain why
        if not hasher.must_update(password_hash):
            return
        messages: list[str] = []

        # 3. Validate salt
        if must_update_salt(decoded["salt"], hasher.salt_entropy):
            messages.append(
                "Password salt seems not to meet the current requirement of "
                f"{hasher.salt_entropy} bits of entropy."
            )

        # 4. Validate parameters
        current = self.current_parameters(hasher)
        provided = {name: decoded[name] for name in current}
        # If it's not the salt, it's the parameters, even unlisted ones (e.g. argon2's hash length)
        if provided != current or not messages:
            messages.append(
                "Password hash parameters do not match authentik's current settings. "
                f"Provided: {provided}. Expected: {current}."
            )

        raise PasswordHashRequiresOverride(messages)

    @classmethod
    def current_parameters(cls, hasher: BasePasswordHasher) -> dict[str, Any]:
        if isinstance(hasher, PBKDF2PasswordHasher):
            return {"iterations": hasher.iterations}
        if isinstance(hasher, Argon2PasswordHasher):
            params = hasher.params()
            return {
                "variety": f"argon2{params.type.name.lower()}",
                "version": params.version,
                "memory_cost": params.memory_cost,
                "time_cost": params.time_cost,
                "parallelism": params.parallelism,
            }
        if isinstance(hasher, BCryptSHA256PasswordHasher):
            return {"work_factor": hasher.rounds}
        if isinstance(hasher, ScryptPasswordHasher):
            return {
                "block_size": hasher.block_size,
                "parallelism": hasher.parallelism,
                "work_factor": hasher.work_factor,
            }
        raise ValueError(f"Unsupported password hasher: {hasher.algorithm}")


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
