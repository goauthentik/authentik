"""Sync LDAP Users and groups into authentik"""

from collections.abc import Generator

from django.conf import settings
from ldap3 import DEREF_ALWAYS, SUBTREE, Connection
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.sources.mapper import SourceMapper
from authentik.lib.config import CONFIG
from authentik.lib.sync.mapper import PropertyMappingManager
from authentik.sources.ldap.models import LDAPSource, flatten
from authentik.tasks.models import Task


class BaseLDAPSynchronizer:
    """Sync LDAP Users and groups into authentik"""

    _source: LDAPSource
    _task: Task
    _logger: BoundLogger
    _connection: Connection
    mapper: SourceMapper
    manager: PropertyMappingManager

    def __init__(self, source: LDAPSource, task: Task):
        self._source = source
        self._task = task
        self._connection = source.connection()
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

    def get_objects(self, **kwargs) -> Generator:
        """Get objects from LDAP, implemented in subclass"""
        raise NotImplementedError()

    def get_attributes(self, object):
        if "attributes" not in object:
            return
        return object.get("attributes", {})

    def get_identifier(self, attributes: dict):
        if not attributes.get(self._source.object_uniqueness_field):
            return
        return flatten(attributes[self._source.object_uniqueness_field])

    def search_paginator(  # noqa: PLR0913
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
        paged_size=None,
        paged_criticality=False,
    ):
        """Search in pages, returns each page"""
        cookie = True
        if not paged_size:
            paged_size = CONFIG.get_int("ldap.page_size", 50)
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
