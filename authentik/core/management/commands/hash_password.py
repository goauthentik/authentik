"""Hash password using Django's password hashers"""

import sys
from getpass import getpass

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _


class Command(BaseCommand):
    """Hash a password using Django's password hashers"""

    help = _("Hash a password for use with AUTHENTIK_BOOTSTRAP_PASSWORD_HASH")

    def add_arguments(self, parser):
        parser.add_argument(
            "password",
            type=str,
            nargs="?",
            help=_("Password to hash. If omitted, prompt for the password."),
        )

    def handle(self, *args, **options):
        password = options["password"]

        if password is None:
            if not sys.stdin.isatty():
                raise CommandError(_("Password prompting requires an interactive terminal"))
            try:
                password = getpass(_("Password: "))
                password_again = getpass(_("Password (again): "))
            except (EOFError, KeyboardInterrupt) as exc:
                raise CommandError(_("Aborted")) from exc
            if password != password_again:
                raise CommandError(_("Passwords do not match"))

        if not password:
            raise CommandError(_("Password cannot be empty"))
        try:
            hashed = make_password(password)
            self.stdout.write(hashed)
        except ValueError as exc:
            raise CommandError(f"{_('Error hashing password')}: {exc}") from exc
