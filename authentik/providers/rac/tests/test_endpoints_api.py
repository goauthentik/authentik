"""Test Endpoints API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_user
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
                "autocomplete": {},
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
                            "assigned_backchannel_application_name": None,
                            "assigned_backchannel_application_slug": None,
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
                "autocomplete": {},
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
                            "assigned_backchannel_application_name": None,
                            "assigned_backchannel_application_slug": None,
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
                            "assigned_backchannel_application_name": None,
                            "assigned_backchannel_application_slug": None,
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

    def test_list_settings_visibility(self):
        """settings can carry connection credentials and is only returned to users
        who can manage the endpoint/provider, not to users listing it to launch."""
        endpoint_secret = generate_id()
        provider_secret = generate_id()
        self.provider.settings = {"password": provider_secret}
        self.provider.save()
        endpoint = Endpoint.objects.create(
            name=f"c-{generate_id()}",
            host=generate_id(),
            protocol=Protocols.RDP,
            auth_mode="static",
            settings={"username": "user", "password": endpoint_secret},
            provider=self.provider,
        )

        # A user who can manage the endpoint receives the stored settings.
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentik_api:endpoint-list"))
        result = next(r for r in response.json()["results"] if r["pk"] == str(endpoint.pk))
        self.assertEqual(result["settings"], {"username": "user", "password": endpoint_secret})
        self.assertEqual(result["provider_obj"]["settings"], {"password": provider_secret})

        # A user without the view permission does not, even though the endpoint is
        # otherwise listed for them.
        user = create_test_user()
        self.assertFalse(user.has_perm("authentik_providers_rac.view_endpoint"))
        self.assertFalse(user.has_perm("authentik_providers_rac.view_racprovider"))
        self.client.force_login(user)
        response = self.client.get(reverse("authentik_api:endpoint-list"))
        result = next(r for r in response.json()["results"] if r["pk"] == str(endpoint.pk))
        self.assertEqual(result["settings"], {})
        self.assertEqual(result["provider_obj"]["settings"], {})
        self.assertNotIn(endpoint_secret, response.content.decode())
        self.assertNotIn(provider_secret, response.content.decode())

    def test_list_regular_user_denied_application(self):
        """A user without object permissions who is denied an endpoint's
        application must not receive that endpoint from the list, even when the
        endpoint itself has no policy bindings."""
        # Gate the application so this user has no path to it.
        PolicyBinding.objects.create(
            target=self.app,
            policy=DummyPolicy.objects.create(
                name=f"deny-{generate_id()}", result=False, wait_min=1, wait_max=2
            ),
            order=0,
        )
        endpoint = Endpoint.objects.create(
            name=f"c-{generate_id()}",
            host=generate_id(),
            protocol=Protocols.RDP,
            auth_mode="static",
            settings={"username": "user", "password": generate_id()},
            provider=self.provider,
        )
        user = create_test_user()
        self.assertFalse(user.has_perm("authentik_providers_rac.view_endpoint"))
        self.client.force_login(user)

        response = self.client.get(reverse("authentik_api:endpoint-list"))
        self.assertEqual(response.status_code, 200)
        pks = [result["pk"] for result in response.json()["results"]]
        self.assertNotIn(str(endpoint.pk), pks)

    def test_list_regular_user_allowed_application(self):
        """A user who passes an application's policies receives its endpoints
        from the list without needing the view_endpoint permission (this is the
        end-user launch picker)."""
        endpoint = Endpoint.objects.create(
            name=f"c-{generate_id()}",
            host=generate_id(),
            protocol=Protocols.RDP,
            provider=self.provider,
        )
        user = create_test_user()
        self.assertFalse(user.has_perm("authentik_providers_rac.view_endpoint"))
        self.client.force_login(user)

        response = self.client.get(reverse("authentik_api:endpoint-list"))
        self.assertEqual(response.status_code, 200)
        pks = [result["pk"] for result in response.json()["results"]]
        self.assertIn(str(endpoint.pk), pks)
