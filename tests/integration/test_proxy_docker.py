"""outpost tests"""

from shutil import rmtree
from tempfile import mkdtemp

import pytest
import yaml
from channels.testing.live import ChannelsLiveServerTestCase
from docker.types.healthcheck import Healthcheck

from authentik.core.tests.utils import create_test_flow
from authentik.crypto.models import CertificateKeyPair
from authentik.outposts.models import (
    DockerServiceConnection,
    Outpost,
    OutpostType,
    default_outpost_config,
)
from authentik.outposts.tasks import outpost_connection_discovery
from authentik.providers.proxy.controllers.docker import DockerController
from authentik.providers.proxy.models import ProxyProvider
from tests.e2e.utils import DockerTestCase, get_docker_tag


class TestProxyDocker(DockerTestCase, ChannelsLiveServerTestCase):
    """Test Docker Controllers"""

    def setUp(self):
        super().setUp()
        self.ssl_folder = mkdtemp()
        self.run_container(
            image="library/docker:dind",
            network_mode="host",
            privileged=True,
            healthcheck=Healthcheck(
                test=["CMD", "docker", "info"],
                interval=5 * 1_000 * 1_000_000,
                start_period=5 * 1_000 * 1_000_000,
            ),
            environment={"DOCKER_TLS_CERTDIR": "/ssl"},
            volumes={
                f"{self.ssl_folder}/": {
                    "bind": "/ssl",
                }
            },
        )
        # Ensure that local connection have been created
        outpost_connection_discovery.send()
        self.provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=create_test_flow(),
        )
        with (
            open(f"{self.ssl_folder}/client/cert.pem", encoding="utf8") as cert,
            open(f"{self.ssl_folder}/client/key.pem", encoding="utf8") as key,
        ):
            authentication_kp = CertificateKeyPair.objects.create(
                name="docker-authentication",
                certificate_data=cert.read(),
                key_data=key.read(),
            )
        with open(f"{self.ssl_folder}/client/ca.pem", encoding="utf8") as authority:
            verification_kp = CertificateKeyPair.objects.create(
                name="docker-verification",
                certificate_data=authority.read(),
            )
        self.service_connection = DockerServiceConnection.objects.create(
            url="https://localhost:2376",
            tls_verification=verification_kp,
            tls_authentication=authentication_kp,
        )
        self.outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
            service_connection=self.service_connection,
            _config=default_outpost_config(self.live_server_url),
        )
        self.outpost.providers.add(self.provider)
        self.outpost.save()

    def tearDown(self) -> None:
        super().tearDown()
        try:
            rmtree(self.ssl_folder)
        except PermissionError:
            pass

    @pytest.mark.timeout(120)
    def test_docker_controller(self):
        """test that deployment requires update"""
        controller = DockerController(self.outpost, self.service_connection)
        controller.up()
        controller.down()

    @pytest.mark.timeout(120)
    def test_docker_static(self):
        """test that deployment requires update"""
        controller = DockerController(self.outpost, self.service_connection)
        manifest = controller.get_static_deployment()
        compose = yaml.load(manifest, Loader=yaml.SafeLoader)
        self.assertEqual(compose["version"], "3.5")
        self.assertEqual(
            compose["services"]["authentik_proxy"]["image"],
            f"ghcr.io/goauthentik/dev-proxy:{get_docker_tag()}",
        )
