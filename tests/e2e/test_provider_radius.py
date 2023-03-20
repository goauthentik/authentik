"""Radius e2e tests"""
from dataclasses import asdict
from sys import platform
from time import sleep
from unittest.case import skipUnless

from docker.client import DockerClient, from_env
from docker.models.containers import Container
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessAccept, AccessReject, AccessRequest

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, User
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id, generate_key
from authentik.outposts.models import Outpost, OutpostConfig, OutpostType
from authentik.providers.radius.models import RadiusProvider
from tests.e2e.utils import SeleniumTestCase, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderRadius(SeleniumTestCase):
    """Radius Outpost e2e tests"""

    radius_container: Container

    def setUp(self):
        super().setUp()
        self.shared_secret = generate_key()

    def tearDown(self) -> None:
        super().tearDown()
        self.output_container_logs(self.radius_container)
        self.radius_container.kill()

    def start_radius(self, outpost: Outpost) -> Container:
        """Start radius container based on outpost created"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image=self.get_container_image("ghcr.io/goauthentik/dev-radius"),
            detach=True,
            network_mode="host",
            environment={
                "AUTHENTIK_HOST": self.live_server_url,
                "AUTHENTIK_TOKEN": outpost.token.key,
            },
        )
        return container

    def _prepare(self) -> User:
        """prepare user, provider, app and container"""
        radius: RadiusProvider = RadiusProvider.objects.create(
            name=generate_id(),
            authorization_flow=Flow.objects.get(slug="default-authentication-flow"),
            shared_secret=self.shared_secret,
        )
        # we need to create an application to actually access radius
        Application.objects.create(name="radius", slug=generate_id(), provider=radius)
        outpost: Outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.RADIUS,
            _config=asdict(OutpostConfig(log_level="debug")),
        )
        outpost.providers.add(radius)

        self.radius_container = self.start_radius(outpost)

        # Wait until outpost healthcheck succeeds
        healthcheck_retries = 0
        while healthcheck_retries < 50:
            if len(outpost.state) > 0:
                state = outpost.state[0]
                if state.last_seen:
                    break
            healthcheck_retries += 1
            sleep(0.5)
        sleep(5)
        return outpost

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_radius_bind_success(self):
        """Test simple bind"""
        self._prepare()
        srv = Client(
            server="localhost",
            secret=self.shared_secret.encode(),
            dict=Dictionary("tests/radius-dictionary"),
        )

        req = srv.CreateAuthPacket(
            code=AccessRequest, User_Name=self.user.username, NAS_Identifier="localhost"
        )
        req["User-Password"] = req.PwCrypt(self.user.username)

        reply = srv.SendPacket(req)
        self.assertEqual(reply.code, AccessAccept)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_radius_bind_fail(self):
        """Test simple bind (failed)"""
        self._prepare()
        srv = Client(
            server="localhost",
            secret=self.shared_secret.encode(),
            dict=Dictionary("tests/radius-dictionary"),
        )

        req = srv.CreateAuthPacket(
            code=AccessRequest, User_Name=self.user.username, NAS_Identifier="localhost"
        )
        req["User-Password"] = req.PwCrypt(self.user.username + "foo")

        reply = srv.SendPacket(req)
        self.assertEqual(reply.code, AccessReject)
