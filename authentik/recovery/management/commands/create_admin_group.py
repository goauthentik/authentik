"""authentik recovery create_admin_group"""

from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from authentik.core.models import User
from authentik.recovery.lib import create_admin_group


class Command(BaseCommand):
    """Create admin group if the default group gets deleted"""

    help = _("Create admin group if the default group gets deleted.")

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("user", action="store", help="User to add to the admin group.")

    def handle(self, *args, **options):
        """Create admin group if the default group gets deleted"""
        username = options.get("user")
        user = User.objects.filter(username=username).first()
        if not user:
            self.stderr.write(f"User '{username}' not found.")
            return
        group = create_admin_group(user)
        self.stdout.write(f"User '{username}' successfully added to the group '{group.name}'.")
