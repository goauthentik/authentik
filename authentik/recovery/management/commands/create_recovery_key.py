"""authentik recovery createkey command"""

from datetime import timedelta
from getpass import getuser

from django.utils.timezone import now
from django.utils.translation import gettext as _

from authentik.core.models import User
from authentik.recovery.lib import create_recovery_token
from authentik.tenants.management import TenantCommand


class Command(TenantCommand):
    """Create Token used to recover access"""

    help = _("Create a Key which can be used to restore access to authentik.")

    def add_arguments(self, parser):
        parser.add_argument(
            "duration",
            default=1,
            action="store",
            help="How long the token is valid for (in years).",
        )
        parser.add_argument("user", action="store", help="Which user the Token gives access to.")

    def handle_per_tenant(self, *args, **options):
        """Create Token used to recover access"""
        duration = int(options.get("duration", 1))
        expiry = now() + timedelta(days=duration * 365.2425)
        user = User.objects.filter(username=options.get("user")).first()
        if not user:
            self.stderr.write(f"User '{options.get('user')}' not found.")
            return
        _, url = create_recovery_token(user, expiry, getuser())
        self.stdout.write(
            f"Store this link safely, as it will allow anyone to access authentik as {user}."
        )
        self.stdout.write(url)
