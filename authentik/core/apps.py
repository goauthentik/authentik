"""authentik core app config"""
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from django.db import DatabaseError, ProgrammingError


class AuthentikCoreConfig(AppConfig):
    """authentik core app config"""

    name = "authentik.core"
    label = "authentik_core"
    verbose_name = "authentik Core"
    mountpoint = ""

    def ready(self):
        import_module("authentik.core.signals")
        if settings.DEBUG:
            from authentik.root.celery import worker_ready_hook

            worker_ready_hook()
        try:
            self.ensure_source_inbuilt()
        except (ProgrammingError, DatabaseError):
            pass

    def ensure_source_inbuilt(self):
        from authentik.core.models import Source

        Source.objects.update_or_create(
            defaults={
                "name": "authentik Built-in",
                "slug": "authentik-built-in",
            },
            managed="goauthentik.io/sources/inbuilt",
        )
