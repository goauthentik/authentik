"""Connection module for storage backends."""

from django.db import connection as db_connection


class Connection:
    """Connection wrapper that provides schema_name attribute."""

    def __init__(self):
        """Initialize connection wrapper."""
        self._schema_name = "public"  # Default schema

    @property
    def schema_name(self) -> str:
        """Get current schema name.

        Returns:
            str: Current schema name from database connection
        """
        return getattr(db_connection, "schema_name", self._schema_name)

    @schema_name.setter
    def schema_name(self, value: str):
        """Set schema name.

        Args:
            value (str): New schema name
        """
        self._schema_name = value
        setattr(db_connection, "schema_name", value)

    @schema_name.deleter
    def schema_name(self):
        """Reset schema name to default."""
        self._schema_name = "public"
        if hasattr(db_connection, "schema_name"):
            delattr(db_connection, "schema_name")


# Create a singleton instance
connection = Connection() 