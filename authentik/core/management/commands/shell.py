"""authentik shell command"""
import code
import platform

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete

from authentik import __version__
from authentik.core.models import User
from authentik.events.middleware import IGNORED_MODELS
from authentik.events.models import Event, EventAction
from authentik.events.utils import model_to_dict

BANNER_TEXT = """### authentik shell ({authentik})
### Node {node} | Arch {arch} | Python {python} """.format(
    node=platform.node(),
    python=platform.python_version(),
    arch=platform.machine(),
    authentik=__version__,
)


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
        namespace = {}

        # Gather Django models and constants from each app
        for app in apps.get_app_configs():
            # Load models from each app
            for model in app.get_models():
                namespace[model.__name__] = model

        return namespace

    @staticmethod
    # pylint: disable=unused-argument
    def post_save_handler(sender, instance: Model, created: bool, **_):
        """Signal handler for all object's post_save"""
        if isinstance(instance, IGNORED_MODELS):
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
    # pylint: disable=unused-argument
    def pre_delete_handler(sender, instance: Model, **_):
        """Signal handler for all object's pre_delete"""
        if isinstance(instance, IGNORED_MODELS):  # pragma: no cover
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
            # pylint: disable=exec-used
            exec(options["command"], namespace)  # nosec # noqa
            return

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
        code.interact(banner=BANNER_TEXT, local=namespace)
