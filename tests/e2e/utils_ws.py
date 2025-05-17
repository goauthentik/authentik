from channels.testing import ChannelsLiveServerTestCase
from daphne.testing import DaphneProcess

from tests.e2e.utils import get_local_ip


def set_database_connection():
    from django.conf import settings

    settings.DATABASES["default"]["NAME"] = settings.DATABASES["default"]["TEST"]["NAME"]
    settings.TEST = True


class DatabasePatchDaphneProcess(DaphneProcess):
    # See https://github.com/django/channels/issues/2048
    # See https://github.com/django/channels/pull/2033

    def __init__(self, host, get_application, kwargs=None, setup=None, teardown=None):
        super().__init__(host, get_application, kwargs, setup, teardown)
        self.setup = set_database_connection


class WebsocketTestCase(ChannelsLiveServerTestCase):

    host = get_local_ip()
    ProtocolServerProcess = DatabasePatchDaphneProcess
