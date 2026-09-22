"""Test SSH connections to devices managed by the authentik agent"""

from django.test import TransactionTestCase
from jwt import decode

from authentik.blueprints.tests import reconcile_app
from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_user
from authentik.endpoints.connectors.agent.models import AgentConnector, AgentDeviceConnection
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import (
    SSH_HOST_KEY_SETTING,
    SSH_TOKEN_SETTING,
    ConnectionToken,
    Protocols,
    RACProvider,
)
from authentik.providers.rac.tests import create_test_device

HOST_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB3sK7tW3qkaMCG1xVX0Nnu7qzK6wvI7zPLp7mDz0MRk"


class TestAgentSSH(TransactionTestCase):
    """Test the settings for devices managed by the authentik agent"""

    def setUp(self):
        self.user = create_test_user()
        self.provider = RACProvider.objects.create(name=generate_id())
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.device = create_test_device(host=generate_id(), protocol=Protocols.SSH)
        session = Session.objects.create(session_key=generate_id(), last_ip="255.255.255.255")
        self.token = ConnectionToken.objects.create(
            provider=self.provider,
            device=self.device,
            protocol=Protocols.SSH,
            session=AuthenticatedSession.objects.create(session=session, user=self.user),
        )

    def enroll(self, host_key: str = HOST_KEY) -> None:
        """Enroll the device with the agent connector"""
        connector = AgentConnector.objects.create(name=generate_id())
        connection = AgentDeviceConnection.objects.create(
            device=self.device,
            connector=connector,
        )
        connection.create_snapshot(
            data={"vendor": {"goauthentik.io/platform": {"ssh_host_keys": [host_key]}}}
        )

    @reconcile_app("authentik_crypto")
    def test_settings(self):
        """An enrolled device is connected to with a token instead of credentials"""
        self.enroll(f"localhost {HOST_KEY}")
        settings = self.token.get_settings()
        self.assertEqual(settings["username"], self.user.username)
        # The host key the agent reported, without the prefix it reports it with
        self.assertEqual(settings[SSH_HOST_KEY_SETTING], HOST_KEY)
        # The outpost turns this into a certificate, the device validates it with us
        token = decode(
            settings[SSH_TOKEN_SETTING],
            options={"verify_signature": False},
            audience=str(self.device.pk),
        )
        self.assertEqual(token["preferred_username"], self.user.username)
        self.assertEqual(token["iss"], "goauthentik.io/platform")

    @reconcile_app("authentik_crypto")
    def test_settings_not_enrolled(self):
        """A device without the agent is connected to with the settings it has"""
        self.assertNotIn(SSH_TOKEN_SETTING, self.token.get_settings())

    @reconcile_app("authentik_crypto")
    def test_settings_other_protocol(self):
        """Only SSH connections use a certificate"""
        self.enroll()
        self.token.protocol = Protocols.RDP
        self.assertNotIn(SSH_TOKEN_SETTING, self.token.get_settings())
