"""Hash password using Django's password hashers"""

import sys
from getpass import getpass

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Hash a password using Django's password hashers"""

    help = "Hash a password for use with AUTHENTIK_BOOTSTRAP_PASSWORD_HASH"

    # Not "stdin": call_command() maps that name onto the --stdin flag's dest.
    stealth_options = ("stdin_stream",)

    def add_arguments(self, parser):
        parser.add_argument(
            "password",
            type=str,
            nargs="?",
            default=None,
            help=(
                "Password to hash. Exposed in the process list and shell history, "
                "so prefer --stdin or the interactive prompt."
            ),
        )
        parser.add_argument(
            "--stdin",
            action="store_true",
            dest="from_stdin",
            help="Read the password from stdin instead of an argument.",
        )

    def execute(self, *args, **options):
        self.stdin = options.get("stdin_stream", sys.stdin)
        return super().execute(*args, **options)

    def handle(self, *args, **options):
        password = self.get_password(options["password"], options["from_stdin"])
        if not password:
            raise CommandError("Password cannot be empty")
        try:
            hashed = make_password(password)
        except ValueError as exc:
            raise CommandError(f"Error hashing password: {exc}") from exc
        self.stdout.write(hashed)

    def get_password(self, password: str | None, from_stdin: bool) -> str:
        """Resolve the password from stdin, an argument, or an interactive prompt."""
        if from_stdin:
            if password is not None:
                raise CommandError("Cannot use both --stdin and a password argument.")
            return self.read_stdin()
        if password is not None:
            return password
        return self.prompt()

    def read_stdin(self) -> str:
        """Read a single line, discarding the trailing newline a pipe usually carries."""
        password = self.stdin.readline()
        return password.removesuffix("\n").removesuffix("\r")

    def prompt(self) -> str:
        """Prompt twice, so a typo fails here instead of in a deployed hash."""
        if not self.stdin.isatty():
            raise CommandError(
                "No password given. Pass the password as an argument, use --stdin to read "
                "it from a pipe, or attach a TTY to be prompted."
            )
        password = getpass("Password: ")
        if password != getpass("Password (again): "):
            raise CommandError("Passwords do not match.")
        return password
