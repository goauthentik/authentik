"""authentik shell command"""

import platform
from pprint import pprint

from django.core.management.commands.shell import Command as BaseCommand
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete

from authentik import authentik_full_version
from authentik.core.models import User
from authentik.events.middleware import should_log_model
from authentik.events.models import Event, EventAction
from authentik.events.utils import model_to_dict


def get_banner_text(shell_type="shell") -> str:
    return f"""### authentik {shell_type} ({authentik_full_version()})
### Node {platform.node()} | Arch {platform.machine()} | Python {platform.python_version()} """


class Command(BaseCommand):
    """Start the Django shell with all authentik models already imported"""

    def get_namespace(self, **options):
        return {
            **super().get_namespace(**options),
            "pprint": pprint,
        }

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
        post_save.connect(Command.post_save_handler)
        pre_delete.connect(Command.pre_delete_handler)

        print(get_banner_text())

        super().handle(**options)
