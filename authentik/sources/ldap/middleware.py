from authentik.lib.sync.middleware import SyncMiddleware
from authentik.sources.ldap.models import LDAPSourceSync
from authentik.sources.ldap.tasks import ldap_sync, ldap_sync_page, ldap_sync_trigger_outgoing_sync


class LDAPSyncMiddleware(SyncMiddleware):
    SyncModel = LDAPSourceSync
    actors = [
        ldap_sync,
        ldap_sync_page,
        ldap_sync_trigger_outgoing_sync,
    ]
