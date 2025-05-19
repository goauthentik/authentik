"""Base classes and mixins for storage backends."""

from django.db import connection
from django.core.files.storage import FileSystemStorage
from structlog.stdlib import get_logger

LOGGER = get_logger()


class TenantAwareStorage:
    """Mixin providing tenant-aware path functionality for storage backends."""

    @property
    def tenant_prefix(self) -> str:
        """Get current tenant schema prefix.

        Returns:
            str: The current tenant's schema name from the database connection.
        """
        return connection.schema_name

    @tenant_prefix.setter
    def tenant_prefix(self, value):
        """Setter for tenant_prefix property.

        This is required for tests that need to set tenant-specific resources.
        It does nothing as the property always returns connection.schema_name,
        but it's needed to prevent AttributeError.
        """
        # This is a no-op, but prevents AttributeError in tests
        # as the property is derived from the connection
        pass

    @tenant_prefix.deleter
    def tenant_prefix(self):
        """Deleter for tenant_prefix property.

        This is required for tests that need to clean up tenant-specific resources.
        """
        # No-op deleter as the tenant_prefix is derived from the connection
        pass

    def get_tenant_path(self, name: str) -> str:
        """Get tenant-specific path for storage.

        Args:
            name (str): Original file path/name.

        Returns:
            str: Path prefixed with tenant identifier for proper isolation.
        """
        return f"{self.tenant_prefix}/{name}"
    
    def _open(self, name, mode="rb"):
        """Stub _open method to support mocking in tests.
        
        This is meant to be overridden by actual storage implementations.
        
        Args:
            name: Name of the file to open
            mode: Mode to open the file in
            
        Raises:
            NotImplementedError: If not overridden by a subclass
        """
        raise NotImplementedError("Storage backend must implement _open")


class DirectoryStructureMixin:
    """Mixin providing directory structure creation functionality for storage backends."""
    
    def _ensure_directory_structure(self):
        """Ensure required directory structure exists.
        
        This is an abstract method that should be implemented by storage backends
        to create their required directory structure.
        """
        raise NotImplementedError("Storage backend must implement _ensure_directory_structure") 