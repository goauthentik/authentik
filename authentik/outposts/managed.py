"""Outpost managed objects"""
from authentik.managed.manager import EnsureExists, ObjectManager
from authentik.outposts.models import Outpost, OutpostType

MANAGED_OUTPOST = "goauthentik.io/outposts/inbuilt"


class OutpostManager(ObjectManager):
    """Outpost managed objects"""

    def reconcile(self):
        return [
            EnsureExists(
                Outpost,
                MANAGED_OUTPOST,
                name="authentik Bundeled Outpost",
                type=OutpostType.PROXY,
            ),
        ]
