"""Outpost managed objects"""
from dataclasses import asdict

from authentik.managed.manager import EnsureExists, ObjectManager
from authentik.outposts.models import Outpost, OutpostConfig, OutpostType

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
                _config=asdict(
                    OutpostConfig(
                        authentik_host="",
                        kubernetes_disabled_components=[
                            "deployment",
                            "service",
                            "secret",
                        ],
                    )
                ),
            ),
        ]
