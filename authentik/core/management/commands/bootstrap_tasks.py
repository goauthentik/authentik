"""Run bootstrap tasks"""

import pydoc
from django.core.management.base import BaseCommand
from django_tenants.utils import get_public_schema_name

from authentik.lib.utils.reflection import get_apps
from authentik.tenants.models import Tenant


class Command(BaseCommand):
    """Run bootstrap tasks to ensure certain objects are created"""

    def handle(self, **options):
        for app in get_apps():
            for task in getattr(app, "startup_tasks_default_tenant", []):
                with Tenant.objects.get(schema_name=get_public_schema_name()):
                    pydoc.locate(task)()

            for task in getattr(app, "startup_tasks_all_tenants", []):
                for tenant in Tenant.objects.filter(ready=True):
                    with tenant:
                        pydoc.locate(task)()
