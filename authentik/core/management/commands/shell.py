"""authentik shell command"""

import code
import platform
import sys
import traceback
from pprint import pprint

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete

from authentik import get_full_version
from authentik.core.models import User
from authentik.events.middleware import should_log_model
from authentik.events.models import Event, EventAction
from authentik.events.utils import model_to_dict


def get_banner_text(shell_type="shell") -> str:
    return f"""### authentik {shell_type} ({get_full_version()})
### Node {platform.node()} | Arch {platform.machine()} | Python {platform.python_version()} """


class Command(BaseCommand):
    """Start the Django shell with all authentik models already imported"""

    django_models = {}

    def add_arguments(self, parser):
        parser.add_argument(
            "-c",
            "--command",
            help="Python code to execute (instead of starting an interactive shell)",
        )

    def get_namespace(self):
        """Prepare namespace with all models"""
        namespace = {
            "pprint": pprint,
        }

        # Gather Django models and constants from each app
        for app in apps.get_app_configs():
            # Load models from each app
            for model in app.get_models():
                namespace[model.__name__] = model

        return namespace

    @staticmethod
    def post_save_handler(sender, instance: Model, created: bool, **_):
        """Signal handler for all object's post_save"""
        if not should_log_model(instance):
            return

        action = EventAction.MODEL_CREATED if created else EventAction.MODEL_UPDATED
        Event.new(action, model=model_to_dict(instance)).set_user(
            User(
                username="authentik-shell",
                pk=0,
                email="",
            )
        ).save()

    @staticmethod
    def pre_delete_handler(sender, instance: Model, **_):
        """Signal handler for all object's pre_delete"""
        if not should_log_model(instance):  # pragma: no cover
            return

        Event.new(EventAction.MODEL_DELETED, model=model_to_dict(instance)).set_user(
            User(
                username="authentik-shell",
                pk=0,
                email="",
            )
        ).save()

    def handle(self, **options):
        namespace = self.get_namespace()

        post_save.connect(Command.post_save_handler)
        pre_delete.connect(Command.pre_delete_handler)

        # If Python code has been passed, execute it and exit.
        if options["command"]:

            exec(options["command"], namespace)  # nosec # noqa
            return

        try:
            hook = sys.__interactivehook__
        except AttributeError:
            # Match the behavior of the cpython shell where a missing
            # sys.__interactivehook__ is ignored.
            pass
        else:
            try:
                hook()
            except Exception:
                # Match the behavior of the cpython shell where an error in
                # sys.__interactivehook__ prints a warning and the exception
                # and continues.
                print("Failed calling sys.__interactivehook__")
                traceback.print_exc()
        # Try to enable tab-complete
        try:
            import readline
            import rlcompleter
        except ModuleNotFoundError:
            pass
        else:
            readline.set_completer(rlcompleter.Completer(namespace).complete)
            readline.parse_and_bind("tab: complete")

        # Run interactive shell
        code.interact(banner=get_banner_text(), local=namespace)
