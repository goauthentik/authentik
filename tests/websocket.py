# This file cannot import anything django or anything that will load django
from sys import stderr

from channels.testing import ChannelsLiveServerTestCase
from daphne.testing import DaphneProcess
from structlog.stdlib import get_logger

from tests import IS_CI, get_local_ip


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


class BaseWebsocketTestCase(ChannelsLiveServerTestCase):
    """Base channels test case"""

    host = get_local_ip()
    ProtocolServerProcess = DatabasePatchDaphneProcess


class WebsocketTestCase(BaseWebsocketTestCase):
    """Test case to allow testing against a running Websocket/HTTP server"""

    def setUp(self):
        if IS_CI:
            print("::group::authentik Logs", file=stderr)
        from django.apps import apps

        from authentik.core.tests.utils import create_test_admin_user

        apps.get_app_config("authentik_tenants").ready()
        self.logger = get_logger()
        self.user = create_test_admin_user()
        super().setUp()

    def tearDown(self):
        if IS_CI:
            print("::endgroup::", file=stderr)
        super().tearDown()
