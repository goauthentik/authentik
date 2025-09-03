"""authentik recovery createkey command"""

from datetime import timedelta
from getpass import getuser

from django.utils.timesince import timesince
from django.utils.timezone import now
from django.utils.translation import gettext as _

from authentik.core.models import User
from authentik.recovery.lib import create_recovery_token
from authentik.tenants.management import TenantCommand


class Command(TenantCommand):
    """Create Token used to recover access"""

    help = _("Create a Key which can be used to restore access to authentik.")

    def format_duration_message(self, duration: int) -> str:
        """Format duration in minutes to a human-readable message"""
        current_time = now()
        future_time = current_time + timedelta(minutes=duration)

        # fyi a non-breaking space is returned by timesince
        return timesince(current_time, future_time)

    def add_arguments(self, parser):
        parser.add_argument(
            "duration",
            nargs="?",
            default=60,
            type=int,
            help="How long the token is valid for (in minutes). Default: 60 minutes (1 hour).",
        )
        parser.add_argument("user", action="store", help="Which user the Token gives access to.")

    def handle_per_tenant(self, *args, **options):
        """Create Token used to recover access"""
        duration = int(options.get("duration", 60))
        expiry = now() + timedelta(minutes=duration)
        user = User.objects.filter(username=options.get("user")).first()
        if not user:
            self.stderr.write(f"User '{options.get('user')}' not found.")
            return
        _, url = create_recovery_token(user, expiry, getuser())

        duration_msg = self.format_duration_message(duration)

        self.stdout.write(
            f"Store this link safely, as it will allow anyone to access authentik as {user}."
        )
        self.stdout.write(f"This recovery token is valid for {duration_msg}.")
        self.stdout.write(url)
