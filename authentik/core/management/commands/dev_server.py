"""custom runserver command"""

from typing import TextIO

from daphne.management.commands.runserver import Command as RunServer
from daphne.server import Server

from authentik.lib.debug import start_debug_server
from authentik.root.signals import post_startup, pre_startup, startup


class SignalServer(Server):
    """Server which signals back to authentik when it finished starting up"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        start_debug_server()

        def ready_callable():
            pre_startup.send(sender=self)
            startup.send(sender=self)
            post_startup.send(sender=self)

        self.ready_callable = ready_callable


class Command(RunServer):
    """custom runserver command, which doesn't show the misleading django startup message"""

    server_cls = SignalServer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Redirect standard stdout banner from Daphne into the void
        # as there are a couple more steps that happen before startup is fully done
        self.stdout = TextIO()
