from sys import stderr

from channels.testing import ChannelsLiveServerTestCase
from django.apps import apps
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from dramatiq import get_broker
from structlog.stdlib import get_logger

from authentik.core.apps import Setup
from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.tasks.test import use_test_broker
from tests._process import TestDatabaseProcess
from tests.decorators import IS_CI, get_local_ip
from tests.docker import DockerTestCase


class E2ETestMixin(DockerTestCase):
    host = get_local_ip()
    user: User
    serve_static = True
    ProtocolServerProcess = TestDatabaseProcess

    def setUp(self):
        if IS_CI:
            print("::group::authentik Logs", file=stderr)
        apps.get_app_config("authentik_tenants").ready()
        self.wait_timeout = 60
        self.logger = get_logger()
        self.user = create_test_admin_user()
        Setup.set(True)
        super().setUp()

    @classmethod
    def _pre_setup(cls):
        use_test_broker()
        return super()._pre_setup()

    def _post_teardown(self):
        broker = get_broker()
        broker.flush_all()
        broker.close()
        return super()._post_teardown()

    def tearDown(self):
        if IS_CI:
            print("::endgroup::", file=stderr)
        super().tearDown()


class E2ETestCase(E2ETestMixin, StaticLiveServerTestCase):
    """E2E Test case with django static live server"""


class ChannelsE2ETestCase(E2ETestMixin, ChannelsLiveServerTestCase):
    """E2E Test case with channels live server (websocket + static)"""
