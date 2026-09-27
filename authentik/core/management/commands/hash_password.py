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
            password = getpass("Password: ")
            password_again = getpass("Password (again): ")
            if password != password_again:
                raise CommandError("Passwords do not match")
        else:
            password = input()

        if not password:
            raise CommandError("Password cannot be empty")
        hashed = make_password(password)
        self.stdout.write(hashed)
