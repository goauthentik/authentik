"""Test RAC Models"""

from django.test import TransactionTestCase

from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.facts import OSFamily
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import (
    ConnectionToken,
    Protocols,
    RACPropertyMapping,
    RACProvider,
    resolve_address,
    resolve_maximum_connections,
    resolve_protocol,
)
from authentik.providers.rac.tests import create_test_device, set_device_facts


class TestResolution(TransactionTestCase):
    """Test how a device's address and protocol are resolved"""

    def setUp(self):
        self.provider = RACProvider.objects.create(name=generate_id())

    def test_address_from_facts_hostname(self):
        """The hostname a device reports is used when it has no override"""
        device = create_test_device()
        set_device_facts(device, {"network": {"hostname": "host.example.com", "interfaces": []}})
        self.assertEqual(resolve_address(device), "host.example.com")

    def test_address_from_facts_interface(self):
        """Without a hostname, the first non-local interface address is used"""
        device = create_test_device()
        set_device_facts(
            device,
            {
                "network": {
                    "interfaces": [
                        {
                            "name": "lo",
                            "hardware_address": "00:00:00:00:00:00",
                            "ip_addresses": ["127.0.0.1", "::1"],
                        },
                        {
                            "name": "eth0",
                            "hardware_address": "aa:bb:cc:dd:ee:ff",
                            "ip_addresses": ["10.0.0.5/24"],
                        },
                    ]
                }
            },
        )
        self.assertEqual(resolve_address(device), "10.0.0.5")

    def test_address_override(self):
        """An explicit host overrides the reported facts"""
        device = create_test_device(host="jump.example.com:3390")
        set_device_facts(device, {"network": {"hostname": "host.example.com"}})
        self.assertEqual(resolve_address(device), "jump.example.com:3390")

    def test_address_missing(self):
        """A device without facts and without an override has no address"""
        self.assertIsNone(resolve_address(create_test_device()))

    def test_protocol_from_os(self):
        """Without any configuration the protocol follows the device's OS"""
        windows = create_test_device()
        set_device_facts(windows, {"os": {"family": OSFamily.windows}})
        self.assertEqual(resolve_protocol(self.provider, windows), Protocols.RDP)

        linux = create_test_device()
        set_device_facts(linux, {"os": {"family": OSFamily.linux}})
        self.assertEqual(resolve_protocol(self.provider, linux), Protocols.SSH)

        self.assertEqual(resolve_protocol(self.provider, create_test_device()), Protocols.SSH)

    def test_protocol_from_provider(self):
        """The provider's protocol takes precedence over the device's OS"""
        self.provider.protocol = Protocols.VNC
        device = create_test_device()
        set_device_facts(device, {"os": {"family": OSFamily.windows}})
        self.assertEqual(resolve_protocol(self.provider, device), Protocols.VNC)

    def test_protocol_override(self):
        """The device's override takes precedence over everything"""
        self.provider.protocol = Protocols.VNC
        device = create_test_device(protocol=Protocols.SSH)
        self.assertEqual(resolve_protocol(self.provider, device), Protocols.SSH)

    def test_maximum_connections(self):
        """The device's override takes precedence over the provider's limit"""
        self.provider.maximum_connections = 3
        self.assertEqual(resolve_maximum_connections(self.provider, create_test_device()), 3)
        self.assertEqual(
            resolve_maximum_connections(
                self.provider, create_test_device(overrides={"maximum_connections": -1})
            ),
            -1,
        )


class TestConnectionSettings(TransactionTestCase):
    """Test how connection settings are merged"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.provider = RACProvider.objects.create(name=generate_id())
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.device = create_test_device(host=f"{generate_id()}:1324", protocol=Protocols.RDP)
        session = Session.objects.create(
            session_key=generate_id(),
            last_ip="255.255.255.255",
        )
        auth_session = AuthenticatedSession.objects.create(session=session, user=self.user)
        self.token = ConnectionToken.objects.create(
            provider=self.provider,
            device=self.device,
            session=auth_session,
        )
        self.host = self.device.attributes["goauthentik.io/rac"]["host"]

    def base_settings(self, **kwargs) -> dict:
        settings = {
            "hostname": self.host.split(":")[0],
            "port": "1324",
            "client-name": f"authentik - {self.user}",
            "drive-path": f"/tmp/connection/{self.token.token}",  # nosec
            "create-drive-path": "true",
            "resize-method": "display-update",
        }
        settings.update(kwargs)
        return settings

    def test_settings_merge(self):
        """Test settings merge"""
        self.assertEqual(self.token.get_settings(), self.base_settings())

        # Set settings in provider
        self.provider.settings = {"level": "provider"}
        self.provider.save()
        self.assertEqual(self.token.get_settings(), self.base_settings(level="provider"))

        # Set settings on the device
        self.device.attributes["goauthentik.io/rac"]["settings"] = {"level": "device"}
        self.device.save()
        self.assertEqual(self.token.get_settings(), self.base_settings(level="device"))

        # Set settings in property mapping (provider)
        mapping = RACPropertyMapping.objects.create(
            name=generate_id(),
            expression="""return {
                "level": "property_mapping_provider"
            }""",
        )
        self.provider.property_mappings.add(mapping)
        self.assertEqual(
            self.token.get_settings(), self.base_settings(level="property_mapping_provider")
        )

        # Set settings in property mapping (device)
        mapping = RACPropertyMapping.objects.create(
            name=generate_id(),
            static_settings={
                "level": "property_mapping_device",
                "foo": True,
                "bar": 6,
            },
        )
        self.device.attributes["goauthentik.io/rac"]["property_mappings"] = [str(mapping.pk)]
        self.device.save()
        self.assertEqual(
            self.token.get_settings(),
            self.base_settings(level="property_mapping_device", foo="true", bar="6"),
        )

        # Set settings in token
        self.token.settings = {"level": "token"}
        self.token.save()
        self.assertEqual(
            self.token.get_settings(),
            self.base_settings(level="token", foo="true", bar="6"),
        )

    def test_settings_address_from_facts(self):
        """A device without an override is connected to on its reported address"""
        device = create_test_device(protocol=Protocols.SSH)
        set_device_facts(device, {"network": {"hostname": "host.example.com"}})
        self.token.device = device
        self.token.save()
        settings = self.token.get_settings()
        self.assertEqual(settings["hostname"], "host.example.com")
        self.assertNotIn("port", settings)
        self.assertNotIn("resize-method", settings)

    def test_settings_port_override(self):
        """The port can be overridden separately from the host"""
        device = create_test_device(overrides={"host": "host.example.com", "port": 2222})
        self.token.device = device
        self.token.save()
        settings = self.token.get_settings()
        self.assertEqual(settings["hostname"], "host.example.com")
        self.assertEqual(settings["port"], "2222")
