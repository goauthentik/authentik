"""Change user type"""

from importlib import import_module

from django.conf import settings

from authentik.tenants.management import TenantCommand


class Command(TenantCommand):
    """Delete all sessions"""

    def handle_per_tenant(self, **options):
        engine = import_module(settings.SESSION_ENGINE)
        engine.SessionStore.clear_expired()
