"""Hash password using Django's password hashers"""

import sys
from getpass import getpass

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Hash a password using Django's password hashers"""

    help = (
        "Hash a password for use with AUTHENTIK_BOOTSTRAP_PASSWORD_HASH. Prompt when "
        "interactive, or read the password from standard input."
    )

    def handle(self, *args, **options):
        if sys.stdin.isatty():
            try:
                password = getpass("Password: ")
                password_again = getpass("Password (again): ")
            except (EOFError, KeyboardInterrupt) as exc:
                raise CommandError("Aborted") from exc
            if password != password_again:
                raise CommandError("Passwords do not match")
        else:
            try:
                password = input()
            except EOFError as exc:
                raise CommandError("Password cannot be empty") from exc

        if not password:
            raise CommandError("Password cannot be empty")
        try:
            hashed = make_password(password)
            self.stdout.write(hashed)
        except ValueError as exc:
            raise CommandError(f"Error hashing password: {exc}") from exc
