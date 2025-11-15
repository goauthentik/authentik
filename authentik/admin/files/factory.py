"""Factory for creating storage backend instances"""

from typing import TYPE_CHECKING

from rest_framework.exceptions import ValidationError
from structlog.stdlib import get_logger

from authentik.admin.files.utils import get_storage_config

if TYPE_CHECKING:
    from authentik.admin.files.backend import Backend, Usage

LOGGER = get_logger()


class BackendFactory:
    """Factory for creating storage backend instances."""

    # Registry of available backends
    _backends: dict[str, type["Backend"]] = {}

    @classmethod
    def register(cls, name: str, backend_class: type["Backend"]) -> None:
        """Register a backend type.

        Args:
            name: Backend identifier (e.g. "file", "s3")
            backend_class: Backend class to register
        """
        cls._backends[name] = backend_class
        LOGGER.debug("Registered backend", name=name, backend_class=backend_class.__name__)

    @classmethod
    def create(cls, usage: "Usage") -> "Backend":
        """Create appropriate backend instance based on configuration.

        Args:
            usage: Usage type enum

        Returns:
            Backend instance

        Raises:
            ValidationError: If backend type is unknown
        """
        backend_type = get_storage_config("backend", "file")

        if backend_type not in cls._backends:
            LOGGER.error(
                "Unknown storage backend configured",
                backend_type=backend_type,
                usage=usage.value,
                available_backends=list(cls._backends.keys()),
            )
            raise ValidationError(f"Unknown storage backend: {backend_type}")

        backend_class = cls._backends[backend_type]
        LOGGER.info(
            "Creating storage backend",
            backend_type=backend_type,
            backend_class=backend_class.__name__,
            usage=usage.value,
        )
        return backend_class(usage)

    @classmethod
    def get_static_backend(cls, usage: "Usage") -> "Backend":
        """Get StaticBackend instance.

        Args:
            usage: Usage type enum

        Returns:
            StaticBackend instance
        """
        from authentik.admin.files.backends import StaticBackend

        return StaticBackend(usage)

    @classmethod
    def get_passthrough_backend(cls, usage: "Usage") -> "Backend":
        """Get PassthroughBackend instance.

        Args:
            usage: Usage type enum

        Returns:
            PassthroughBackend instance
        """
        from authentik.admin.files.backends import PassthroughBackend

        return PassthroughBackend(usage)


def _register_default_backends():
    """Register the default backend implementations."""
    from authentik.admin.files.backends import FileBackend, S3Backend

    BackendFactory.register("file", FileBackend)
    BackendFactory.register("s3", S3Backend)


# Register default backends on module import
_register_default_backends()
