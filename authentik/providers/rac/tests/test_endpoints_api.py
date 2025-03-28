"""Test Endpoints API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.rac.models import Endpoint, Protocols, RACProvider


class TestEndpointsAPI(APITestCase):
    """Test endpoints API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.provider = RACProvider.objects.create(
            name=generate_id(),
        )
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.allowed = Endpoint.objects.create(
            name=f"a-{generate_id()}",
            host=generate_id(),
            protocol=Protocols.RDP,
            provider=self.provider,
        )
        self.denied = Endpoint.objects.create(
            name=f"b-{generate_id()}",
            host=generate_id(),
            protocol=Protocols.RDP,
            provider=self.provider,
        )
        PolicyBinding.objects.create(
            target=self.denied,
            policy=DummyPolicy.objects.create(name="deny", result=False, wait_min=1, wait_max=2),
            order=0,
        )

    def test_list(self):
        """Test list operation without superuser_full_list"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentik_api:endpoint-list"))
        self.assertJSONEqual(
            response.content.decode(),
            {
                "pagination": {
                    "next": 0,
                    "previous": 0,
                    "count": 2,
                    "current": 1,
                    "total_pages": 1,
                    "start_index": 1,
                    "end_index": 2,
                },
                "results": [
                    {
                        "pk": str(self.allowed.pk),
                        "name": self.allowed.name,
                        "provider": self.provider.pk,
                        "provider_obj": {
                            "pk": self.provider.pk,
                            "name": self.provider.name,
                            "authentication_flow": None,
                            "authorization_flow": None,
                            "property_mappings": [],
                            "connection_expiry": "hours=8",
                            "delete_token_on_disconnect": False,
                            "component": "ak-provider-rac-form",
                            "assigned_application_slug": self.app.slug,
                            "assigned_application_name": self.app.name,
                            "assigned_backchannel_application_slug": "",
                            "assigned_backchannel_application_name": "",
                            "verbose_name": "RAC Provider",
                            "verbose_name_plural": "RAC Providers",
                            "meta_model_name": "authentik_providers_rac.racprovider",
                            "settings": {},
                            "outpost_set": [],
                        },
                        "protocol": "rdp",
                        "host": self.allowed.host,
                        "maximum_connections": 1,
                        "settings": {},
                        "property_mappings": [],
                        "auth_mode": "",
                        "launch_url": f"/application/rac/{self.app.slug}/{str(self.allowed.pk)}/",
                    },
                ],
            },
        )

    def test_list_superuser_full_list(self):
        """Test list operation with superuser_full_list"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("authentik_api:endpoint-list") + "?superuser_full_list=true"
        )
        self.assertJSONEqual(
            response.content.decode(),
            {
                "pagination": {
                    "next": 0,
                    "previous": 0,
                    "count": 2,
                    "current": 1,
                    "total_pages": 1,
                    "start_index": 1,
                    "end_index": 2,
                },
                "results": [
                    {
                        "pk": str(self.allowed.pk),
                        "name": self.allowed.name,
                        "provider": self.provider.pk,
                        "provider_obj": {
                            "pk": self.provider.pk,
                            "name": self.provider.name,
                            "authentication_flow": None,
                            "authorization_flow": None,
                            "property_mappings": [],
                            "component": "ak-provider-rac-form",
                            "assigned_application_slug": self.app.slug,
                            "assigned_application_name": self.app.name,
                            "assigned_backchannel_application_slug": "",
                            "assigned_backchannel_application_name": "",
                            "connection_expiry": "hours=8",
                            "delete_token_on_disconnect": False,
                            "verbose_name": "RAC Provider",
                            "verbose_name_plural": "RAC Providers",
                            "meta_model_name": "authentik_providers_rac.racprovider",
                            "settings": {},
                            "outpost_set": [],
                        },
                        "protocol": "rdp",
                        "host": self.allowed.host,
                        "maximum_connections": 1,
                        "settings": {},
                        "property_mappings": [],
                        "auth_mode": "",
                        "launch_url": f"/application/rac/{self.app.slug}/{str(self.allowed.pk)}/",
                    },
                    {
                        "pk": str(self.denied.pk),
                        "name": self.denied.name,
                        "provider": self.provider.pk,
                        "provider_obj": {
                            "pk": self.provider.pk,
                            "name": self.provider.name,
                            "authentication_flow": None,
                            "authorization_flow": None,
                            "property_mappings": [],
                            "component": "ak-provider-rac-form",
                            "assigned_application_slug": self.app.slug,
                            "assigned_application_name": self.app.name,
                            "assigned_backchannel_application_slug": "",
                            "assigned_backchannel_application_name": "",
                            "connection_expiry": "hours=8",
                            "delete_token_on_disconnect": False,
                            "verbose_name": "RAC Provider",
                            "verbose_name_plural": "RAC Providers",
                            "meta_model_name": "authentik_providers_rac.racprovider",
                            "settings": {},
                            "outpost_set": [],
                        },
                        "protocol": "rdp",
                        "host": self.denied.host,
                        "maximum_connections": 1,
                        "settings": {},
                        "property_mappings": [],
                        "auth_mode": "",
                        "launch_url": f"/application/rac/{self.app.slug}/{str(self.denied.pk)}/",
                    },
                ],
            },
        )
