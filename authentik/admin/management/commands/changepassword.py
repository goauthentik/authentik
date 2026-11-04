"""Change a user's password"""

from getpass import getpass

from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from authentik.core.models import User
from authentik.stages.password.models import PasswordDevice


class Command(BaseCommand):
    """Change a user's password, replacing Django's command that writes to the user"""

    help = "Change a user's password."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, username: str, **options):
        user = User.objects.filter(username=username).first()
        if not user:
            raise CommandError(f"User '{username}' does not exist")
        password = getpass("Password: ")
        if password != getpass("Password (again): "):
            raise CommandError("Passwords do not match")
        if not password:
            raise CommandError("Password cannot be empty")
        try:
            PasswordDevice.set_password(user, password)
        except ValidationError as exc:
            # An LDAP or Kerberos source refused the password
            raise CommandError(str(exc)) from exc
        self.stdout.write(f"Password changed for user '{username}'")
