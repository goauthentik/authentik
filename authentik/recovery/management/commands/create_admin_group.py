"""authentik recovery create_admin_group"""
from django.utils.translation import gettext as _

from authentik.core.models import Group, User
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
        group, _ = Group.objects.update_or_create(
            name="authentik Admins",
            defaults={
                "is_superuser": True,
            },
        )
        group.users.add(user)
        self.stdout.write(f"User '{username}' successfully added to the group 'authentik Admins'.")
