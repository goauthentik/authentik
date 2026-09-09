from collections.abc import Iterable

from dramatiq.actor import Actor

from authentik.lib.sync.middleware import SyncMiddleware
from authentik.sources.kerberos.models import KerberosSourceSync


class KerberosSyncMiddleware(SyncMiddleware):
    SyncModel = KerberosSourceSync

    @staticmethod
    def sync_actors() -> Iterable[Actor]:
        from authentik.sources.kerberos.tasks import (
            kerberos_sync,
        )

        return (kerberos_sync,)
