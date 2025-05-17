"""Radius e2e tests"""

from dataclasses import asdict

from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessAccept, AccessReject, AccessRequest

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, User
from authentik.core.tests.utils import create_test_user
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id, generate_key
from authentik.outposts.models import Outpost, OutpostConfig, OutpostType
from authentik.providers.radius.models import RadiusProvider
from tests.decorators import retry
from tests.docker import DockerTestCase
from tests.websocket import WebsocketTestCase


class TestProviderRadius(DockerTestCase, WebsocketTestCase):
    """Radius Outpost e2e tests"""

    def setUp(self):
        super().setUp()
        self.shared_secret = generate_key()

    def start_radius(self, outpost: Outpost):
        """Start radius container based on outpost created"""
        self.run_container(
            image=self.get_container_image("ghcr.io/goauthentik/dev-radius"),
            ports={"1812/udp": "1812/udp"},
            environment={"AUTHENTIK_TOKEN": outpost.token.key},
        )
        self.wait_for_outpost(outpost)

    def _prepare(self) -> User:
        """prepare user, provider, app and container"""
        self.user = create_test_user()
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

        self.start_radius(outpost)
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
            dict=Dictionary("authentik/providers/radius/dictionaries/dictionary"),
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
            dict=Dictionary("authentik/providers/radius/dictionaries/dictionary"),
        )

        req = srv.CreateAuthPacket(
            code=AccessRequest, User_Name=self.user.username, NAS_Identifier="localhost"
        )
        req["User-Password"] = req.PwCrypt(self.user.username + "foo")

        reply = srv.SendPacket(req)
        self.assertEqual(reply.code, AccessReject)
