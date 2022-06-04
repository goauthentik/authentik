"""Test Applications API"""
from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import OAuth2Provider


class TestApplicationsAPI(APITestCase):
    """Test applications API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.provider = OAuth2Provider.objects.create(
            name="test",
            redirect_uris="http://some-other-domain",
            authorization_flow=Flow.objects.create(
                name="test",
                slug="test",
            ),
        )
        self.allowed = Application.objects.create(
            name="allowed",
            slug="allowed",
            meta_launch_url="https://goauthentik.io/%(username)s",
            open_in_new_tab=True,
            provider=self.provider,
        )
        self.denied = Application.objects.create(name="denied", slug="denied")
        PolicyBinding.objects.create(
            target=self.denied,
            policy=DummyPolicy.objects.create(name="deny", result=False, wait_min=1, wait_max=2),
            order=0,
        )

    def test_check_access(self):
        """Test check_access operation"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "authentik_api:application-check-access",
                kwargs={"slug": self.allowed.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["passing"], True)
        self.assertEqual(body["messages"], [])
        self.assertEqual(len(body["log_messages"]), 0)
        response = self.client.get(
            reverse(
                "authentik_api:application-check-access",
                kwargs={"slug": self.denied.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["passing"], False)
        self.assertEqual(body["messages"], ["dummy"])

    def test_list(self):
        """Test list operation without superuser_full_list"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentik_api:application-list"))
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
                        "name": "allowed",
                        "slug": "allowed",
                        "group": "",
                        "provider": self.provider.pk,
                        "provider_obj": {
                            "assigned_application_name": "allowed",
                            "assigned_application_slug": "allowed",
                            "authorization_flow": str(self.provider.authorization_flow.pk),
                            "component": "ak-provider-oauth2-form",
                            "meta_model_name": "authentik_providers_oauth2.oauth2provider",
                            "name": self.provider.name,
                            "pk": self.provider.pk,
                            "property_mappings": [],
                            "verbose_name": "OAuth2/OpenID Provider",
                            "verbose_name_plural": "OAuth2/OpenID Providers",
                        },
                        "launch_url": f"https://goauthentik.io/{self.user.username}",
                        "meta_launch_url": "https://goauthentik.io/%(username)s",
                        "open_in_new_tab": True,
                        "meta_icon": None,
                        "meta_description": "",
                        "meta_publisher": "",
                        "policy_engine_mode": "any",
                    },
                ],
            },
        )

    def test_list_superuser_full_list(self):
        """Test list operation with superuser_full_list"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("authentik_api:application-list") + "?superuser_full_list=true"
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
                        "name": "allowed",
                        "slug": "allowed",
                        "group": "",
                        "provider": self.provider.pk,
                        "provider_obj": {
                            "assigned_application_name": "allowed",
                            "assigned_application_slug": "allowed",
                            "authorization_flow": str(self.provider.authorization_flow.pk),
                            "component": "ak-provider-oauth2-form",
                            "meta_model_name": "authentik_providers_oauth2.oauth2provider",
                            "name": self.provider.name,
                            "pk": self.provider.pk,
                            "property_mappings": [],
                            "verbose_name": "OAuth2/OpenID Provider",
                            "verbose_name_plural": "OAuth2/OpenID Providers",
                        },
                        "launch_url": f"https://goauthentik.io/{self.user.username}",
                        "meta_launch_url": "https://goauthentik.io/%(username)s",
                        "open_in_new_tab": True,
                        "meta_icon": None,
                        "meta_description": "",
                        "meta_publisher": "",
                        "policy_engine_mode": "any",
                    },
                    {
                        "launch_url": None,
                        "meta_description": "",
                        "meta_icon": None,
                        "meta_launch_url": "",
                        "open_in_new_tab": False,
                        "meta_publisher": "",
                        "group": "",
                        "name": "denied",
                        "pk": str(self.denied.pk),
                        "policy_engine_mode": "any",
                        "provider": None,
                        "provider_obj": None,
                        "slug": "denied",
                    },
                ],
            },
        )
