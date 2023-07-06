"""Sync LDAP Users and groups into authentik"""
from typing import Any, Generator

from django.conf import settings
from django.db.models.base import Model
from django.db.models.query import QuerySet
from ldap3 import DEREF_ALWAYS, SUBTREE, Connection
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.events.models import Event, EventAction
from authentik.lib.merge import MERGE_LIST_UNIQUE
from authentik.sources.ldap.auth import LDAP_DISTINGUISHED_NAME
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource

LDAP_UNIQUENESS = "ldap_uniq"


class BaseLDAPSynchronizer:
    """Sync LDAP Users and groups into authentik"""

    _source: LDAPSource
    _logger: BoundLogger
    _connection: Connection
    _messages: list[str]

    def __init__(self, source: LDAPSource):
        self._source = source
        self._connection = source.connection()
        self._messages = []
        self._logger = get_logger().bind(source=source, syncer=self.__class__.__name__)

    @staticmethod
    def name() -> str:
        """UI name for the type of object this class synchronizes"""
        raise NotImplementedError

    def sync_full(self):
        """Run full sync, this function should only be used in tests"""
        if not settings.TEST:  # noqa
            raise RuntimeError(
                f"{self.__class__.__name__}.sync_full() should only be used in tests"
            )
        for page in self.get_objects():
            self.sync(page)

    def sync(self, page_data: list) -> int:
        """Sync function, implemented in subclass"""
        raise NotImplementedError()

    @property
    def messages(self) -> list[str]:
        """Get all UI messages"""
        return self._messages

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

    def message(self, *args, **kwargs):
        """Add message that is later added to the System Task and shown to the user"""
        formatted_message = " ".join(args)
        if "dn" in kwargs:
            formatted_message += f"; DN: {kwargs['dn']}"
        self._messages.append(formatted_message)
        self._logger.warning(*args, **kwargs)

    def get_objects(self, **kwargs) -> Generator:
        """Get objects from LDAP, implemented in subclass"""
        raise NotImplementedError()

    # pylint: disable=too-many-arguments
    def search_paginator(
        self,
        search_base,
        search_filter,
        search_scope=SUBTREE,
        dereference_aliases=DEREF_ALWAYS,
        attributes=None,
        size_limit=0,
        time_limit=0,
        types_only=False,
        get_operational_attributes=False,
        controls=None,
        paged_size=5,
        paged_criticality=False,
    ):
        """Search in pages, returns each page"""
        cookie = True
        while cookie:
            self._connection.search(
                search_base,
                search_filter,
                search_scope,
                dereference_aliases,
                attributes,
                size_limit,
                time_limit,
                types_only,
                get_operational_attributes,
                controls,
                paged_size,
                paged_criticality,
                None if cookie is True else cookie,
            )
            try:
                cookie = self._connection.result["controls"]["1.2.840.113556.1.4.319"]["value"][
                    "cookie"
                ]
            except KeyError:
                cookie = None
            yield self._connection.response

    def _flatten(self, value: Any) -> Any:
        """Flatten `value` if its a list"""
        if isinstance(value, list):
            if len(value) < 1:
                return None
            return value[0]
        return value

    def build_user_properties(self, user_dn: str, **kwargs) -> dict[str, Any]:
        """Build attributes for User object based on property mappings."""
        props = self._build_object_properties(user_dn, self._source.property_mappings, **kwargs)
        props["path"] = self._source.get_user_path()
        return props

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
                value = mapping.evaluate(user=None, request=None, ldap=kwargs, dn=object_dn)
                if value is None:
                    continue
                if isinstance(value, (bytes)):
                    continue
                object_field = mapping.object_field
                if object_field.startswith("attributes."):
                    # Because returning a list might desired, we can't
                    # rely on self._flatten here. Instead, just save the result as-is
                    properties["attributes"][object_field.replace("attributes.", "")] = value
                else:
                    properties[object_field] = self._flatten(value)
            except PropertyMappingExpressionException as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=f"Failed to evaluate property-mapping: '{mapping.name}'",
                    source=self._source,
                    mapping=mapping,
                ).save()
                self._logger.warning("Mapping failed to evaluate", exc=exc, mapping=mapping)
                continue
        if self._source.object_uniqueness_field in kwargs:
            properties["attributes"][LDAP_UNIQUENESS] = self._flatten(
                kwargs.get(self._source.object_uniqueness_field)
            )
        properties["attributes"][LDAP_DISTINGUISHED_NAME] = object_dn
        return properties

    def update_or_create_attributes(
        self,
        obj: type[Model],
        query: dict[str, Any],
        data: dict[str, Any],
    ) -> tuple[Model, bool]:
        """Same as django's update_or_create but correctly update attributes by merging dicts"""
        instance = obj.objects.filter(**query).first()
        if not instance:
            return (obj.objects.create(**data), True)
        for key, value in data.items():
            if key == "attributes":
                continue
            setattr(instance, key, value)
        final_attributes = {}
        MERGE_LIST_UNIQUE.merge(final_attributes, instance.attributes)
        MERGE_LIST_UNIQUE.merge(final_attributes, data.get("attributes", {}))
        instance.attributes = final_attributes
        instance.save()
        return (instance, False)
