from textwrap import fill

from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import force_str

from authentik.stages.authenticator.plugins.otp_static.lib import add_static_token, get_user_model


class Command(BaseCommand):
    help = fill(
        "Adds a single static OTP token to the given user. "
        "The token will be added to an arbitrary static device "
        "attached to the user, creating one if necessary.",
        width=78,
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-t",
            "--token",
            dest="token",
            help="The token to add. If omitted, one will be randomly generated.",
        )
        parser.add_argument("username", help="The user to which the token will be assigned.")

    def handle(self, *args, **options):
        username = options["username"]

        try:
            statictoken = add_static_token(username, options.get("token"))
        except get_user_model().DoesNotExist:
            raise CommandError('User "{0}" does not exist.'.format(username))

        self.stdout.write(force_str(statictoken.token))
