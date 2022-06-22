"""Core managed objects"""
from authentik.core.models import Source
from authentik.managed.manager import EnsureExists, ObjectManager


class CoreManager(ObjectManager):
    """Core managed objects"""

    def reconcile(self):
        return [
            EnsureExists(
                Source,
                "goauthentik.io/sources/inbuilt",
                name="authentik Built-in",
                slug="authentik-built-in",
            ),
        ]
