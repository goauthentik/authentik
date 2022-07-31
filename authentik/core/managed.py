"""Core managed objects"""
from authentik.blueprints.manager import EnsureExists, ObjectManager
from authentik.core.models import Source


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
