"""Test RAC Models"""

from django.test import TransactionTestCase

from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user
from authentik.endpoints.connectors.agent.controller import AgentConnectorController
from authentik.lib.generators import generate_id
from authentik.providers.rac.models import (
    ConnectionToken,
    Protocols,
    RACPropertyMapping,
    RACProvider,
    address_settings,
    available_protocols,
)
from authentik.providers.rac.tests import create_test_device, set_device_facts


class TestConnectionResolution(TransactionTestCase):
    """Test how the address and protocol of a device are resolved"""

    def test_address_from_facts_hostname(self):
        """The hostname an enrolled device reports is used"""
        device = create_test_device()
        set_device_facts(device, {"network": {"hostname": "host.example.com", "interfaces": []}})
        self.assertEqual(address_settings(device), {"hostname": "host.example.com"})

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
        self.assertEqual(address_settings(device), {"hostname": "10.0.0.5"})

    def test_address_from_override(self):
        """A connection override takes precedence over reported facts"""
        device = create_test_device(host="jump.example.com")
        set_device_facts(device, {"network": {"hostname": "host.example.com"}})
        self.assertEqual(address_settings(device), {"hostname": "jump.example.com"})

    def test_address_with_port(self):
        """A port in the address is passed on separately"""
        self.assertEqual(
            address_settings(create_test_device(host="host.example.com:3390")),
            {"hostname": "host.example.com", "port": "3390"},
        )

    def test_address_ipv6(self):
        """The colons of an IPv6 address are not a port"""
        self.assertEqual(
            address_settings(create_test_device(host="2001:db8::1")),
            {"hostname": "2001:db8::1"},
        )

    def test_address_missing(self):
        """A device without facts and without an override has no address"""
        self.assertEqual(address_settings(create_test_device()), {})

    def test_protocols_from_override(self):
        """A connection override sets the protocol of its device"""
        device = create_test_device(host=generate_id(), protocol=Protocols.SSH)
        self.assertEqual(available_protocols(device), [Protocols.SSH])

    def test_protocols_from_agent_facts(self):
        """The agent reports what the device accepts connections on"""
        rdp = create_test_device()
        set_device_facts(
            rdp,
            {
                "vendor": {
                    AgentConnectorController.vendor_identifier(): {
                        "rdp_cert_fingerprint": "aa:bb",
                        "ssh_host_keys": [],
                    }
                }
            },
        )
        self.assertEqual(available_protocols(rdp), [Protocols.RDP])

        ssh = create_test_device()
        set_device_facts(
            ssh,
            {
                "vendor": {
                    AgentConnectorController.vendor_identifier(): {
                        "rdp_cert_fingerprint": "",
                        "ssh_host_keys": ["localhost ssh-ed25519 AAAA"],
                    }
                }
            },
        )
        self.assertEqual(available_protocols(ssh), [Protocols.SSH])

        both = create_test_device()
        set_device_facts(
            both,
            {
                "vendor": {
                    AgentConnectorController.vendor_identifier(): {
                        "rdp_cert_fingerprint": "aa:bb",
                        "ssh_host_keys": ["localhost ssh-ed25519 AAAA"],
                    }
                }
            },
        )
        self.assertEqual(available_protocols(both), [Protocols.RDP, Protocols.SSH])

    def test_protocols_unknown(self):
        """A device that says nothing about itself can be connected to with either"""
        self.assertEqual(available_protocols(create_test_device()), [Protocols.RDP, Protocols.SSH])


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
        self.host = generate_id()
        self.device = create_test_device(host=f"{self.host}:1324", protocol=Protocols.RDP)
        session = Session.objects.create(
            session_key=generate_id(),
            last_ip="255.255.255.255",
        )
        auth_session = AuthenticatedSession.objects.create(session=session, user=self.user)
        self.token = ConnectionToken.objects.create(
            provider=self.provider,
            device=self.device,
            protocol=Protocols.RDP,
            session=auth_session,
        )

    def base_settings(self, **kwargs) -> dict:
        settings = {
            "hostname": self.host,
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

        # Set settings in a property mapping
        mapping = RACPropertyMapping.objects.create(
            name=generate_id(),
            expression="""return {
                "level": "property_mapping"
            }""",
        )
        self.provider.property_mappings.add(mapping)
        self.assertEqual(self.token.get_settings(), self.base_settings(level="property_mapping"))

        # Property mappings receive the device, so they can be device-specific
        mapping.expression = """return {
            "level": "property_mapping",
            "device-name": device.name,
            "foo": True,
            "bar": 6,
        }"""
        mapping.save()
        self.assertEqual(
            self.token.get_settings(),
            self.base_settings(
                level="property_mapping",
                **{"device-name": self.device.name, "foo": "true", "bar": "6"},
            ),
        )

        # Set settings in token
        self.token.settings = {"level": "token"}
        self.token.save()
        settings = self.token.get_settings()
        self.assertEqual(settings["level"], "token")
        self.assertEqual(settings["device-name"], self.device.name)

    def test_settings_protocol_specific(self):
        """The RDP-only settings are not set for other protocols"""
        self.token.protocol = Protocols.SSH
        self.assertNotIn("resize-method", self.token.get_settings())

    def test_settings_without_address(self):
        """A device without an address has no hostname to connect to"""
        self.token.device = create_test_device()
        self.token.save()
        self.assertNotIn("hostname", self.token.get_settings())
