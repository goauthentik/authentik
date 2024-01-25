"""Run bootstrap tasks"""
from django.core.management.base import BaseCommand
from django_tenants.utils import get_public_schema_name

from authentik.root.celery import _get_startup_tasks_all_tenants, _get_startup_tasks_default_tenant
from authentik.tenants.models import Tenant


class Command(BaseCommand):
    """Run bootstrap tasks to ensure certain objects are created"""

    def handle(self, **options):
        for task in _get_startup_tasks_default_tenant():
            with Tenant.objects.get(schema_name=get_public_schema_name()):
                task()

        for task in _get_startup_tasks_all_tenants():
            for tenant in Tenant.objects.filter(ready=True):
                with tenant:
                    task()
