"""Outpost managed objects"""
from authentik.managed.manager import EnsureExists, ObjectManager
from authentik.outposts.models import Outpost, OutpostType

MANAGED_OUTPOST = "goauthentik.io/outposts/embedded"


class OutpostManager(ObjectManager):
    """Outpost managed objects"""

    def reconcile(self):
        return [
            EnsureExists(
                Outpost,
                MANAGED_OUTPOST,
                name="authentik Embedded Outpost",
                type=OutpostType.PROXY,
            ),
        ]
