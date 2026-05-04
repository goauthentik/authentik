from os import unlink, write
from sys import stderr
from tempfile import mkstemp
from urllib.parse import urlencode

from channels.testing import ChannelsLiveServerTestCase
from django.apps import apps
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from dramatiq import get_broker
from structlog.stdlib import get_logger
from yaml import safe_dump

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

    def url(self, view: str, query: dict | None = None, **kwargs) -> str:
        """reverse `view` with `**kwargs` into full URL using live_server_url"""
        url = self.live_server_url + reverse(view, kwargs=kwargs)
        if query:
            return url + "?" + urlencode(query)
        return url


class SSLLiveMixin(DockerTestCase):
    """Mixin to provide an SSL-enabled webserver for integration/e2e tests that require it.

    Overrides `live_server_url` and as such other all usual helper functions will return an HTTPS
    URL. Certificate is self-signed and random on each run."""

    def setUp(self):
        super().setUp()
        self._setup_traefik()

    def tearDown(self):
        super().tearDown()
        unlink(self._traefik_config)

    @property
    def live_server_url(self):
        return f"https://{self.host}:{self._traefik_port}"

    def _setup_traefik(self):
        config = {
            "http": {
                "routers": {
                    "authentik": {
                        "rule": "PathPrefix(`/`)",
                        "entryPoints": ["websecure"],
                        "service": "authentik",
                        "tls": {},
                    }
                },
                "services": {
                    "authentik": {"loadBalancer": {"servers": [{"url": super().live_server_url}]}}
                },
            }
        }
        fd, self._traefik_config = mkstemp()
        write(fd, safe_dump(config).encode())
        traefik = self.run_container(
            image="docker.io/library/traefik:3.1",
            command=[
                "--providers.file.filename=/etc/traefik/dynamic.yml",
                "--providers.file.watch=true",
                "--entrypoints.websecure.address=:9443",
                "--log.level=DEBUG",
                "--api=true",
                "--api.dashboard=true",
                "--api.insecure=true",
            ],
            ports={
                "9443": None,
            },
            volumes={
                self._traefik_config: {
                    "bind": "/etc/traefik/dynamic.yml",
                }
            },
        )
        # {
        #     "8443/tcp": [
        #         {"HostIp": "0.0.0.0", "HostPort": "8443"},
        #         {"HostIp": "::", "HostPort": "8443"},
        #     ],
        # }
        self._traefik_port = traefik.ports["9443/tcp"][0]["HostPort"]


class E2ETestCase(E2ETestMixin, StaticLiveServerTestCase):
    """E2E Test case with django static live server"""


class ChannelsE2ETestCase(E2ETestMixin, ChannelsLiveServerTestCase):
    """E2E Test case with channels live server (websocket + static)"""
