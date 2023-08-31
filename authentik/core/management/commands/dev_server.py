"""custom runserver command"""
from django.core.management.commands.runserver import Command as RunServer


class Command(RunServer):
    """custom runserver command, which doesn't show the misleading django startup message"""

    def on_bind(self, server_port):
        pass
