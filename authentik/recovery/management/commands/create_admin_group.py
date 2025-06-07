"""authentik recovery create_admin_group"""

from django.utils.translation import gettext as _

from authentik.core.models import User
from authentik.recovery.lib import create_admin_group
from authentik.tenants.management import TenantCommand


class Command(TenantCommand):
    """Create admin group if the default group gets deleted"""

    help = _("Create admin group if the default group gets deleted.")

    def add_arguments(self, parser):
        parser.add_argument("user", action="store", help="User to add to the admin group.")

    def handle_per_tenant(self, *args, **options):
        """Create admin group if the default group gets deleted"""
        username = options.get("user")
        user = User.objects.filter(username=username).first()
        if not user:
            self.stderr.write(f"User '{username}' not found.")
            return
        group = create_admin_group(user)
        self.stdout.write(f"User '{username}' successfully added to the group '{group.name}'.")
