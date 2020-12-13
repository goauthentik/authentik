"""outpost tests"""
from shutil import rmtree
from tempfile import mkdtemp
from time import sleep

from django.test import TestCase
from docker import DockerClient, from_env
from docker.models.containers import Container
from docker.types.healthcheck import Healthcheck

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.outposts.apps import AuthentikOutpostConfig
from authentik.outposts.controllers.docker import DockerController
from authentik.outposts.models import DockerServiceConnection, Outpost, OutpostType
from authentik.providers.proxy.models import ProxyProvider


class OutpostDockerTests(TestCase):
    """Test Docker Controllers"""

    def _start_container(self, ssl_folder: str) -> Container:
        client: DockerClient = from_env()
        container = client.containers.run(
            image="docker.beryju.org/proxy/library/docker:dind",
            detach=True,
            network_mode="host",
            remove=True,
            privileged=True,
            healthcheck=Healthcheck(
                test=["CMD", "docker", "info"],
                interval=5 * 100 * 1000000,
                start_period=5 * 100 * 1000000,
            ),
            environment={"DOCKER_TLS_CERTDIR": "/ssl"},
            volumes={
                f"{ssl_folder}/": {
                    "bind": "/ssl",
                }
            },
        )
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            sleep(1)

    def setUp(self):
        super().setUp()
        self.ssl_folder = mkdtemp()
        self.container = self._start_container(self.ssl_folder)
        # Ensure that local connection have been created
        AuthentikOutpostConfig.init_local_connection()
        self.provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=Flow.objects.first(),
        )
        authentication_kp = CertificateKeyPair.objects.create(
            name="docker-authentication",
            certificate_data=open(f"{self.ssl_folder}/client/cert.pem").read(),
            key_data=open(f"{self.ssl_folder}/client/key.pem").read(),
        )
        verification_kp = CertificateKeyPair.objects.create(
            name="docker-verification",
            certificate_data=open(f"{self.ssl_folder}/client/ca.pem").read(),
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
        )
        self.outpost.providers.add(self.provider)
        self.outpost.save()

    def tearDown(self) -> None:
        super().tearDown()
        self.container.kill()
        rmtree(self.ssl_folder)

    def test_docker_controller(self):
        """test that deployment requires update"""
        controller = DockerController(self.outpost, self.service_connection)
        controller.up()
        controller.down()
