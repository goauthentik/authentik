"""Change user type"""

from authentik.core.models import Session
from authentik.tenants.management import TenantCommand


class Command(TenantCommand):
    """Delete all sessions"""

    def handle_per_tenant(self, **options):
        Session.objects.all().delete()
