"""SCIM Client tests"""

from django.core.cache import cache
from django.test import TestCase
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.lib.generators import generate_id
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.providers.scim.tasks import scim_sync


class SCIMClientTests(TestCase):
    """SCIM Client tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Clear cache before each test
        cache.clear()
        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
        )
        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)
        self.provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        self.provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )

    def test_config(self):
        """Test valid config:
        https://docs.aws.amazon.com/singlesignon/latest/developerguide/serviceproviderconfig.html"""
        with Mocker() as mock:
            mock: Mocker
            mock.get(
                "https://localhost/ServiceProviderConfig",
                json={
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
                    "documentationUri": (
                        "https://docs.aws.amazon.com/singlesignon/latest/"
                        "userguide/manage-your-identity-source-idp.html"
                    ),
                    "authenticationSchemes": [
                        {
                            "type": "oauthbearertoken",
                            "name": "OAuth Bearer Token",
                            "description": (
                                "Authentication scheme using the OAuth Bearer Token Standard"
                            ),
                            "specUri": "https://www.rfc-editor.org/info/rfc6750",
                            "documentationUri": (
                                "https://docs.aws.amazon.com/singlesignon/latest/"
                                "userguide/provision-automatically.html"
                            ),
                            "primary": True,
                        }
                    ],
                    "patch": {"supported": True},
                    "bulk": {"supported": False, "maxOperations": 1, "maxPayloadSize": 1048576},
                    "filter": {"supported": True, "maxResults": 50},
                    "changePassword": {"supported": False},
                    "sort": {"supported": False},
                    "etag": {"supported": False},
                },
            )
            SCIMClient(self.provider)
            self.assertEqual(mock.call_count, 1)
            self.assertEqual(mock.request_history[0].method, "GET")

    def test_config_invalid(self):
        """Test invalid config"""
        with Mocker() as mock:
            mock: Mocker
            mock.get(
                "https://localhost/ServiceProviderConfig",
                json={},
            )
            SCIMClient(self.provider)
            self.assertEqual(mock.call_count, 1)
            self.assertEqual(mock.request_history[0].method, "GET")

    def test_scim_sync(self):
        """test scim_sync task"""
        scim_sync.send(self.provider.pk).get_result()

    def test_config_caching(self):
        """Test that ServiceProviderConfig is cached after first successful fetch"""
        config_json = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
            "documentationUri": "https://example.com/docs",
            "authenticationSchemes": [
                {
                    "type": "oauthbearertoken",
                    "name": "OAuth Bearer Token",
                    "description": "OAuth Bearer Token",
                    "specUri": "https://www.rfc-editor.org/info/rfc6750",
                    "documentationUri": "https://example.com/auth",
                    "primary": True,
                }
            ],
            "patch": {"supported": True},
            "bulk": {"supported": False, "maxOperations": 1, "maxPayloadSize": 1048576},
            "filter": {"supported": True, "maxResults": 50},
            "changePassword": {"supported": False},
            "sort": {"supported": False},
            "etag": {"supported": False},
        }

        with Mocker() as mock:
            mock.get("https://localhost/ServiceProviderConfig", json=config_json)

            client = SCIMClient(self.provider)

            # First call should hit the API
            config1 = client.get_service_provider_config()
            self.assertEqual(mock.call_count, 1)

            # Second call should use cache, no additional API call
            config2 = client.get_service_provider_config()
            self.assertEqual(mock.call_count, 1)  # Still 1, not 2

            # Verify both configs are the same
            self.assertEqual(config1, config2)

    def test_config_caching_invalid(self):
        """Test that default config is cached when remote config is invalid"""
        with Mocker() as mock:
            mock.get("https://localhost/ServiceProviderConfig", json={})

            client = SCIMClient(self.provider)

            # First call should hit the API and get invalid response
            config1 = client.get_service_provider_config()
            self.assertEqual(mock.call_count, 1)

            # Second call should use cached default config, no additional API call
            config2 = client.get_service_provider_config()
            self.assertEqual(mock.call_count, 1)  # Still 1, not 2

            # Verify both configs are the same default
            self.assertEqual(config1, config2)

    def test_config_caching_error(self):
        """Test that default config is cached when remote request fails"""
        with Mocker() as mock:
            mock.get("https://localhost/ServiceProviderConfig", status_code=500)

            client = SCIMClient(self.provider)

            # First call should hit the API and fail
            config1 = client.get_service_provider_config()
            self.assertEqual(mock.call_count, 1)

            # Second call should use cached default config, no additional API call
            config2 = client.get_service_provider_config()
            self.assertEqual(mock.call_count, 1)  # Still 1, not 2

            # Verify both configs are the same default
            self.assertEqual(config1, config2)

    def test_config_cache_invalidation_on_save(self):
        """Test that ServiceProviderConfig cache is cleared when provider is saved"""
        config_json = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
            "documentationUri": "https://example.com/docs",
            "authenticationSchemes": [
                {
                    "type": "oauthbearertoken",
                    "name": "OAuth Bearer Token",
                    "description": "OAuth Bearer Token",
                    "specUri": "https://www.rfc-editor.org/info/rfc6750",
                    "documentationUri": "https://example.com/auth",
                    "primary": True,
                }
            ],
            "patch": {"supported": True},
            "bulk": {"supported": False, "maxOperations": 1, "maxPayloadSize": 1048576},
            "filter": {"supported": True, "maxResults": 50},
            "changePassword": {"supported": False},
            "sort": {"supported": False},
            "etag": {"supported": False},
        }

        with Mocker() as mock:
            mock.get("https://localhost/ServiceProviderConfig", json=config_json)

            # First client instantiation caches the config
            SCIMClient(self.provider)
            self.assertEqual(mock.call_count, 1)

            # Creating another client should use cached config
            SCIMClient(self.provider)
            self.assertEqual(mock.call_count, 1)  # Still 1, using cache

            # Save the provider (e.g., changing compatibility mode)
            self.provider.compatibility_mode = "aws"
            self.provider.save()

            # Creating a new client should now hit the API again since cache was cleared
            SCIMClient(self.provider)
            self.assertEqual(mock.call_count, 2)  # New API call after cache invalidation
