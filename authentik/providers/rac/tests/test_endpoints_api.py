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

    def test_list_user_with_model_permissions_sees_endpoints(self):
        """A user with model-level RAC permissions (e.g. view_endpoint)
        must see all endpoints in the list, even those for applications they have
        no access to. This fixes the regression introduced by the security backport
        that filtered the entire list by application access, which broke users
        who only had model-level permissions but no application-level
        access.

        Sensitive fields (settings) are still redacted for users without the
        per-instance view_endpoint permission, preserving the security fix."""
        # Gate the application so the user has no application access.
        PolicyBinding.objects.create(
            target=self.app,
            policy=DummyPolicy.objects.create(
                name=f"deny-{generate_id()}", result=False, wait_min=1, wait_max=2
            ),
            order=0,
        )

        # Create a user with model-level view permission but no
        # application access (the denied policy above blocks it).
        user = create_test_user()
        from django.contrib.auth.models import Permission

        perm = Permission.objects.get(
            content_type__app_label="authentik_providers_rac",
            codename="view_endpoint",
        )
        user.user_permissions.add(perm)

        self.assertFalse(
            user.has_perm("authentik_providers_rac.view_application", self.app)
        )
        self.client.force_login(user)

        response = self.client.get(reverse("authentik_api:endpoint-list"))
        self.assertEqual(response.status_code, 200)
        pks = [r["pk"] for r in response.json()["results"]]
        # The user MUST see the endpoint despite having no app access.
        self.assertIn(str(self.allowed.pk), pks)
        # And also the denied endpoint, because it has model-level permission.
        self.assertIn(str(self.denied.pk), pks)

    def test_list_user_with_model_permissions_settings_redacted(self):
        """A user with model-level view_endpoint permission must
        receive the settings only for endpoints where it also has the
        per-instance view_permission.

        This ensures the security fix (redacting sensitive settings) is
        preserved for users that manage endpoints globally
        but should not see credentials for all of them."""
        endpoint_secret = generate_id()
        endpoint = Endpoint.objects.create(
            name=f"c-{generate_id()}",
            host=generate_id(),
            protocol=Protocols.RDP,
            auth_mode="static",
            settings={"username": "user", "password": endpoint_secret},
            provider=self.provider,
        )

        # Create a user with model-level view permission.
        user = create_test_user()
        from django.contrib.auth.models import Permission

        perm = Permission.objects.get(
            content_type__app_label="authentik_providers_rac",
            codename="view_endpoint",
        )
        user.user_permissions.add(perm)

        # user has model-level permission but NOT per-instance permission
        # for the endpoint (no guardian grant).
        self.assertFalse(
            user.has_perm("authentik_providers_rac.view_endpoint", endpoint)
        )

        self.client.force_login(user)

        response = self.client.get(reverse("authentik_api:endpoint-list"))
        self.assertEqual(response.status_code, 200)
        result = next(
            r for r in response.json()["results"] if r["pk"] == str(endpoint.pk)
        )

        # The endpoint is in the list (model-level permission grants visibility).
        # But settings must be redacted (no per-instance view_permission).
        self.assertEqual(result["settings"], {})
        self.assertNotIn(endpoint_secret, response.content.decode())

    def test_list_user_with_change_permission_sees_endpoints(self):
        """A user with model-level change_endpoint permission
        must see all endpoints in the list. This is the permission that
        the original issue (#24154) reported as broken."""
        PolicyBinding.objects.create(
            target=self.app,
            policy=DummyPolicy.objects.create(
                name=f"deny-{generate_id()}", result=False, wait_min=1, wait_max=2
            ),
            order=0,
        )

        user = create_test_user()
        from django.contrib.auth.models import Permission

        perm = Permission.objects.get(
            content_type__app_label="authentik_providers_rac",
            codename="change_endpoint",
        )
        user.user_permissions.add(perm)

        self.client.force_login(user)

        response = self.client.get(reverse("authentik_api:endpoint-list"))
        self.assertEqual(response.status_code, 200)
        pks = [r["pk"] for r in response.json()["results"]]
        self.assertIn(str(self.allowed.pk), pks)
        self.assertIn(str(self.denied.pk), pks)

    def test_list_user_with_delete_permission_sees_endpoints(self):
        """A user with model-level delete_endpoint permission
        must see all endpoints in the list."""
        user = create_test_user()
        from django.contrib.auth.models import Permission

        perm = Permission.objects.get(
            content_type__app_label="authentik_providers_rac",
            codename="delete_endpoint",
        )
        user.user_permissions.add(perm)

        self.client.force_login(user)

        response = self.client.get(reverse("authentik_api:endpoint-list"))
        self.assertEqual(response.status_code, 200)
        pks = [r["pk"] for r in response.json()["results"]]
        self.assertIn(str(self.allowed.pk), pks)
        self.assertIn(str(self.denied.pk), pks)

    def test_list_user_with_add_permission_sees_endpoints(self):
        """A user with model-level add_endpoint permission
        must see all endpoints in the list."""
        user = create_test_user()
        from django.contrib.auth.models import Permission

        perm = Permission.objects.get(
            content_type__app_label="authentik_providers_rac",
            codename="add_endpoint",
        )
        user.user_permissions.add(perm)

        self.client.force_login(user)

        response = self.client.get(reverse("authentik_api:endpoint-list"))
        self.assertEqual(response.status_code, 200)
        pks = [r["pk"] for r in response.json()["results"]]
        self.assertIn(str(self.allowed.pk), pks)
        self.assertIn(str(self.denied.pk), pks)
