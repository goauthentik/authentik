"""Sync LDAP Users and groups into authentik"""
from structlog.stdlib import BoundLogger, get_logger

from authentik.sources.ldap.models import LDAPSource

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

    def sync(self):
        """Sync function, implemented in subclass"""
        raise NotImplementedError()
