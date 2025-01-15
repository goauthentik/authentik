"""authentik e2e testing utilities"""

import traceback

from daphne.testing import DaphneProcess, _reinstall_reactor
from django import setup as django_setup
from django.conf import settings


class TestDatabaseProcess(DaphneProcess):
    """Channels does not correctly switch to the test database by default.
    https://github.com/django/channels/issues/2048"""

    def run(self):
        # OK, now we are in a forked child process, and want to use the reactor.
        # However, FreeBSD systems like MacOS do not fork the underlying Kqueue,
        # which asyncio (hence asyncioreactor) is built on.
        # Therefore, we should uninstall the broken reactor and install a new one.
        _reinstall_reactor()

        if not settings.configured:  # Fix For raise AppRegistryNotReady("Apps aren't loaded yet.")
            django_setup()  # Ensure Django is fully set up before using settings

        from daphne.endpoints import build_endpoint_description_strings
        from daphne.server import Server
        from twisted.internet import reactor

        application = self.get_application()
        if not settings.DATABASES[list(settings.DATABASES.keys())[0]]["NAME"].startswith("test_"):
            for _, db_settings in settings.DATABASES.items():
                db_settings["NAME"] = f"test_{db_settings['NAME']}"
        settings.TEST = True

        try:
            # Create the server class
            endpoints = build_endpoint_description_strings(host=self.host, port=0)
            self.server = Server(
                application=application, endpoints=endpoints, signal_handlers=False, **self.kwargs
            )
            # Set up a poller to look for the port
            reactor.callLater(0.1, self.resolve_port)
            # Run with setup/teardown
            if self.setup is not None:
                self.setup()
            try:
                self.server.run()
            finally:
                if self.teardown is not None:
                    self.teardown()
        except BaseException as e:
            # Put the error on our queue so the parent gets it
            self.errors.put((e, traceback.format_exc()))
