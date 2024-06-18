"""Test RAC Models"""

from django.test import TransactionTestCase

from authentik.core.models import Application, AuthenticatedSession
from authentik.core.tests.utils import create_test_admin_user
from authentik.enterprise.providers.rac.models import (
    ConnectionToken,
    Endpoint,
    Protocols,
    RACPropertyMapping,
    RACProvider,
)
from authentik.lib.generators import generate_id


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

    def test_settings_merge(self):
        """Test settings merge"""
        token = ConnectionToken.objects.create(
            provider=self.provider,
            endpoint=self.endpoint,
            session=AuthenticatedSession.objects.create(
                user=self.user,
                session_key=generate_id(),
            ),
        )
        path = f"/tmp/connection/{token.token}"  # nosec
        self.assertEqual(
            token.get_settings(),
            {
                "hostname": self.endpoint.host.split(":")[0],
                "port": "1324",
                "client-name": "authentik",
                "drive-path": path,
                "create-drive-path": "true",
            },
        )
        # Set settings in provider
        self.provider.settings = {"level": "provider"}
        self.provider.save()
        self.assertEqual(
            token.get_settings(),
            {
                "hostname": self.endpoint.host.split(":")[0],
                "port": "1324",
                "client-name": "authentik",
                "drive-path": path,
                "create-drive-path": "true",
                "level": "provider",
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
                "hostname": self.endpoint.host.split(":")[0],
                "port": "1324",
                "client-name": "authentik",
                "drive-path": path,
                "create-drive-path": "true",
                "level": "endpoint",
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
                "hostname": self.endpoint.host.split(":")[0],
                "port": "1324",
                "client-name": "authentik",
                "drive-path": path,
                "create-drive-path": "true",
                "level": "token",
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
                "hostname": self.endpoint.host.split(":")[0],
                "port": "1324",
                "client-name": "authentik",
                "drive-path": path,
                "create-drive-path": "true",
                "level": "property_mapping_provider",
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
                "hostname": self.endpoint.host.split(":")[0],
                "port": "1324",
                "client-name": "authentik",
                "drive-path": path,
                "create-drive-path": "true",
                "level": "property_mapping_endpoint",
                "foo": "true",
                "bar": "6",
            },
        )
