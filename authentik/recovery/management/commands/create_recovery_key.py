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

    # Constants for time conversions
    MINUTES_PER_HOUR = 60
    MINUTES_PER_DAY = 1440

    def format_duration_message(self, duration: int) -> str:
        """Format duration in minutes to a human-readable message"""
        if duration == 1:
            return "1 minute"
        elif duration < self.MINUTES_PER_HOUR:
            return f"{duration} minutes"
        elif duration == self.MINUTES_PER_HOUR:
            return "1 hour"
        elif duration < self.MINUTES_PER_DAY:
            hours = duration // self.MINUTES_PER_HOUR
            remaining_minutes = duration % self.MINUTES_PER_HOUR
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                hour_part = f"{hours} hour{'s' if hours > 1 else ''}"
                minute_part = f"{remaining_minutes} minute{'s' if remaining_minutes > 1 else ''}"
                return f"{hour_part} and {minute_part}"
        else:
            days = duration // self.MINUTES_PER_DAY
            remaining_hours = (duration % self.MINUTES_PER_DAY) // self.MINUTES_PER_HOUR
            remaining_minutes = duration % self.MINUTES_PER_HOUR
            duration_parts = []
            if days > 0:
                duration_parts.append(f"{days} day{'s' if days > 1 else ''}")
            if remaining_hours > 0:
                duration_parts.append(f"{remaining_hours} hour{'s' if remaining_hours > 1 else ''}")
            if remaining_minutes > 0:
                duration_parts.append(
                    f"{remaining_minutes} minute{'s' if remaining_minutes > 1 else ''}"
                )

            # Join with commas and "and" for the last element
            parts_count = len(duration_parts)
            if parts_count == 1:
                return duration_parts[0]
            elif parts_count == 2:  # noqa: PLR2004
                return " and ".join(duration_parts)
            else:
                return ", ".join(duration_parts[:-1]) + " and " + duration_parts[-1]

    def add_arguments(self, parser):
        parser.add_argument(
            "duration",
            nargs="?",
            default=self.MINUTES_PER_HOUR,
            type=int,
            help="How long the token is valid for (in minutes). Default: 60 minutes (1 hour).",
        )
        parser.add_argument("user", action="store", help="Which user the Token gives access to.")

    def handle_per_tenant(self, *args, **options):
        """Create Token used to recover access"""
        duration = int(options.get("duration", self.MINUTES_PER_HOUR))
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
