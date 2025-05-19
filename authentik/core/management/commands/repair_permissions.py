"""Repair missing permissions"""

from django.apps import apps
from django.contrib.auth.management import create_permissions
from django.core.management import call_command
from django.core.management.base import BaseCommand, no_translations
from guardian.management import create_anonymous_user

from authentik.tenants.models import Tenant


class Command(BaseCommand):
    """Repair missing permissions"""

    @no_translations
    def handle(self, *args, **options):
        """Check permissions for all apps"""
        for tenant in Tenant.objects.filter(ready=True):
            with tenant:
                # See https://code.djangoproject.com/ticket/28417
                # Remove potential lingering old permissions
                call_command("remove_stale_contenttypes", "--no-input")

                for app in apps.get_app_configs():
                    self.stdout.write(f"Checking app {app.name} ({app.label})\n")
                    create_permissions(app, verbosity=0)
                create_anonymous_user(None, using="default")
