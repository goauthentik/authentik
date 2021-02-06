"""Sync LDAP Users and groups into authentik"""
from typing import Any

from django.db.models.query import QuerySet
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.sources.ldap.auth import LDAP_DISTINGUISHED_NAME
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource

LDAP_UNIQUENESS = "ldap_uniq"


class BaseLDAPSynchronizer:
    """Sync LDAP Users and groups into authentik"""

    _source: LDAPSource
    _logger: BoundLogger

    def __init__(self, source: LDAPSource):
        self._source = source
        self._logger = get_logger().bind(source=source)

    @property
    def base_dn_users(self) -> str:
        """Shortcut to get full base_dn for user lookups"""
        if self._source.additional_user_dn:
            return f"{self._source.additional_user_dn},{self._source.base_dn}"
        return self._source.base_dn

    @property
    def base_dn_groups(self) -> str:
        """Shortcut to get full base_dn for group lookups"""
        if self._source.additional_group_dn:
            return f"{self._source.additional_group_dn},{self._source.base_dn}"
        return self._source.base_dn

    def sync(self) -> int:
        """Sync function, implemented in subclass"""
        raise NotImplementedError()

    def _flatten(self, value: Any) -> Any:
        """Flatten `value` if its a list"""
        if isinstance(value, list):
            if len(value) < 1:
                return None
            return value[0]
        return value

    def build_user_properties(self, user_dn: str, **kwargs) -> dict[str, Any]:
        """Build attributes for User object based on property mappings."""
        return self._build_object_properties(
            user_dn, self._source.property_mappings, **kwargs
        )

    def build_group_properties(self, group_dn: str, **kwargs) -> dict[str, Any]:
        """Build attributes for Group object based on property mappings."""
        return self._build_object_properties(
            group_dn, self._source.property_mappings_group, **kwargs
        )

    def _build_object_properties(
        self, object_dn: str, mappings: QuerySet, **kwargs
    ) -> dict[str, dict[Any, Any]]:
        properties = {"attributes": {}}
        for mapping in mappings.all().select_subclasses():
            if not isinstance(mapping, LDAPPropertyMapping):
                continue
            mapping: LDAPPropertyMapping
            try:
                value = mapping.evaluate(
                    user=None, request=None, ldap=kwargs, dn=object_dn
                )
                if value is None:
                    continue
                object_field = mapping.object_field
                if object_field.startswith("attributes."):
                    # Because returning a list might desired, we can't
                    # rely on self._flatten here. Instead, just save the result as-is
                    properties["attributes"][
                        object_field.replace("attributes.", "")
                    ] = value
                else:
                    properties[object_field] = self._flatten(value)
            except PropertyMappingExpressionException as exc:
                self._logger.warning(
                    "Mapping failed to evaluate", exc=exc, mapping=mapping
                )
                continue
        if self._source.object_uniqueness_field in kwargs:
            properties["attributes"][LDAP_UNIQUENESS] = self._flatten(
                kwargs.get(self._source.object_uniqueness_field)
            )
        properties["attributes"][LDAP_DISTINGUISHED_NAME] = object_dn
        return properties
