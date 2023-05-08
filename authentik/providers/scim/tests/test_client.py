"""SCIM Client tests"""
from django.test import TestCase
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.lib.generators import generate_id
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.providers.scim.tasks import scim_sync_all


class SCIMClientTests(TestCase):
    """SCIM Client tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
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

    def test_scim_sync_all(self):
        """test scim_sync_all task"""
        scim_sync_all()
