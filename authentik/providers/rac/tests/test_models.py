"""Test RAC Models"""

from django.test import SimpleTestCase, TransactionTestCase

from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import (
    ConnectionToken,
    Endpoint,
    Protocols,
    RACPropertyMapping,
    RACProvider,
)


class TestParseHost(SimpleTestCase):
    """Test host parsing"""

    def test_hosts(self):
        """Test host parsing for all supported forms"""
        cases = {
            # DNS name / IPv4
            "host.example": ("host.example", None),
            "host.example:5901": ("host.example", "5901"),
            "192.0.2.10:5901": ("192.0.2.10", "5901"),
            # IPv6 literals: bracketed (with/without port) and bare
            "[2001:db8::10c]:5901": ("2001:db8::10c", "5901"),
            "[2001:db8::10c]": ("2001:db8::10c", None),
            "2001:db8::10c": ("2001:db8::10c", None),
        }
        for host, expected in cases.items():
            with self.subTest(host=host):
                self.assertEqual(ConnectionToken.parse_host(host), expected)

    def test_hostname_lowercased(self):
        """Test hostname is normalized to lowercase"""
        self.assertEqual(ConnectionToken.parse_host("Host.Example:5901"), ("host.example", "5901"))


class TestModels(TransactionTestCase):
    """Test RAC Models"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.provider = RACProvider.objects.create(
            name=generate_id(),
        )
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.endpoint = Endpoint.objects.create(
            name=generate_id(),
            host=f"{generate_id()}:1324",
            protocol=Protocols.RDP,
            provider=self.provider,
        )

    def test_settings_ipv6_host(self):
        """Test settings with IPv6 host"""
        endpoint = Endpoint.objects.create(
            name=generate_id(),
            host="[2001:db8::10c]:5901",
            protocol=Protocols.VNC,
            provider=self.provider,
        )
        session = Session.objects.create(
            session_key=generate_id(),
            last_ip="255.255.255.255",
        )
        auth_session = AuthenticatedSession.objects.create(session=session, user=self.user)
        token = ConnectionToken.objects.create(
            provider=self.provider,
            endpoint=endpoint,
            session=auth_session,
        )
        settings = token.get_settings()
        self.assertEqual(settings["hostname"], "2001:db8::10c")
        self.assertEqual(settings["port"], "5901")

    def test_settings_merge(self):
        """Test settings merge"""
        session = Session.objects.create(
            session_key=generate_id(),
            last_ip="255.255.255.255",
        )
        auth_session = AuthenticatedSession.objects.create(session=session, user=self.user)
        token = ConnectionToken.objects.create(
            provider=self.provider,
            endpoint=self.endpoint,
            session=auth_session,
        )
        path = f"/tmp/connection/{token.token}"  # nosec
        self.assertEqual(
            token.get_settings(),
            {
                "hostname": self.endpoint.host.split(":")[0].lower(),
                "port": "1324",
                "client-name": f"authentik - {self.user}",
                "drive-path": path,
                "create-drive-path": "true",
                "resize-method": "display-update",
            },
        )
        # Set settings in provider
        self.provider.settings = {"level": "provider"}
        self.provider.save()
        self.assertEqual(
            token.get_settings(),
            {
                "hostname": self.endpoint.host.split(":")[0].lower(),
                "port": "1324",
                "client-name": f"authentik - {self.user}",
                "drive-path": path,
                "create-drive-path": "true",
                "level": "provider",
                "resize-method": "display-update",
            },
        )
        # Set settings in endpoint
        self.endpoint.settings = {
            "level": "endpoint",
        }
        self.endpoint.save()
        self.assertEqual(
            token.get_settings(),
            {
                "hostname": self.endpoint.host.split(":")[0].lower(),
                "port": "1324",
                "client-name": f"authentik - {self.user}",
                "drive-path": path,
                "create-drive-path": "true",
                "level": "endpoint",
                "resize-method": "display-update",
            },
        )
        # Set settings in property mapping (provider)
        mapping = RACPropertyMapping.objects.create(
            name=generate_id(),
            expression="""return {
                "level": "property_mapping_provider"
            }""",
        )
        self.provider.property_mappings.add(mapping)
        self.assertEqual(
            token.get_settings(),
            {
                "hostname": self.endpoint.host.split(":")[0].lower(),
                "port": "1324",
                "client-name": f"authentik - {self.user}",
                "drive-path": path,
                "create-drive-path": "true",
                "level": "property_mapping_provider",
                "resize-method": "display-update",
            },
        )
        # Set settings in property mapping (endpoint)
        mapping = RACPropertyMapping.objects.create(
            name=generate_id(),
            static_settings={
                "level": "property_mapping_endpoint",
                "foo": True,
                "bar": 6,
            },
        )
        self.endpoint.property_mappings.add(mapping)
        self.assertEqual(
            token.get_settings(),
            {
                "hostname": self.endpoint.host.split(":")[0].lower(),
                "port": "1324",
                "client-name": f"authentik - {self.user}",
                "drive-path": path,
                "create-drive-path": "true",
                "level": "property_mapping_endpoint",
                "foo": "true",
                "bar": "6",
                "resize-method": "display-update",
            },
        )
        # Set settings in token
        token.settings = {
            "level": "token",
        }
        token.save()
        self.assertEqual(
            token.get_settings(),
            {
                "hostname": self.endpoint.host.split(":")[0].lower(),
                "port": "1324",
                "client-name": f"authentik - {self.user}",
                "drive-path": path,
                "create-drive-path": "true",
                "foo": "true",
                "bar": "6",
                "resize-method": "display-update",
                "level": "token",
            },
        )
