"""Hash password using Django's password hashers"""

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Hash a password using Django's password hashers"""

    help = "Hash a password for use with AUTHENTIK_BOOTSTRAP_PASSWORD_HASH"

    def add_arguments(self, parser):
        parser.add_argument(
            "password",
            type=str,
            help="Password to hash",
        )

    def handle(self, *args, **options):
        password = options["password"]

        if not password:
            raise CommandError("Password cannot be empty")


        try:
            hashed = make_password(password)
            if not hashed:
                raise CommandError("Failed to hash password")
            self.stdout.write(hashed)
        except Exception as exc:
            raise CommandError(f"Error hashing password: {exc}") from exc
