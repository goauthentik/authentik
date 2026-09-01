from collections.abc import Iterable

from dramatiq.actor import Actor

from authentik.lib.sync.middleware import SyncMiddleware
from authentik.sources.ldap.models import LDAPSourceSync


class LDAPSyncMiddleware(SyncMiddleware):
    SyncModel = LDAPSourceSync

    @staticmethod
    def sync_actors() -> Iterable[Actor]:
        from authentik.sources.ldap.tasks import (
            ldap_sync,
            ldap_sync_page,
            ldap_sync_trigger_outgoing_sync,
        )

        return (
            ldap_sync,
            ldap_sync_page,
            ldap_sync_trigger_outgoing_sync,
        )
