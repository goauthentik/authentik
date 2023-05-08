"""Test Applications API"""
from json import loads

from django.core.files.base import ContentFile
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
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
            authorization_flow=create_test_flow(),
        )
        self.allowed: Application = Application.objects.create(
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

    def test_formatted_launch_url(self):
        """Test formatted launch URL"""
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.patch(
                reverse("authentik_api:application-detail", kwargs={"slug": self.allowed.slug}),
                {"meta_launch_url": "https://%(username)s-test.test.goauthentik.io/%(username)s"},
            ).status_code,
            200,
        )
        self.allowed.refresh_from_db()
        self.assertEqual(
            self.allowed.get_launch_url(self.user),
            f"https://{self.user.username}-test.test.goauthentik.io/{self.user.username}",
        )

    def test_set_icon(self):
        """Test set_icon"""
        file = ContentFile(b"text", "name")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "authentik_api:application-set-icon",
                kwargs={"slug": self.allowed.slug},
            ),
            data=encode_multipart(data={"file": file}, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 200)

        app_raw = self.client.get(
            reverse(
                "authentik_api:application-detail",
                kwargs={"slug": self.allowed.slug},
            ),
        )
        app = loads(app_raw.content)
        self.allowed.refresh_from_db()
        self.assertEqual(self.allowed.get_meta_icon, app["meta_icon"])
        self.assertEqual(self.allowed.meta_icon.read(), b"text")

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
                            "authentication_flow": None,
                            "authorization_flow": str(self.provider.authorization_flow.pk),
                            "component": "ak-provider-oauth2-form",
                            "meta_model_name": "authentik_providers_oauth2.oauth2provider",
                            "name": self.provider.name,
                            "pk": self.provider.pk,
                            "property_mappings": [],
                            "verbose_name": "OAuth2/OpenID Provider",
                            "verbose_name_plural": "OAuth2/OpenID Providers",
                        },
                        "backchannel_providers": [],
                        "backchannel_providers_obj": [],
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
                            "authentication_flow": None,
                            "authorization_flow": str(self.provider.authorization_flow.pk),
                            "component": "ak-provider-oauth2-form",
                            "meta_model_name": "authentik_providers_oauth2.oauth2provider",
                            "name": self.provider.name,
                            "pk": self.provider.pk,
                            "property_mappings": [],
                            "verbose_name": "OAuth2/OpenID Provider",
                            "verbose_name_plural": "OAuth2/OpenID Providers",
                        },
                        "backchannel_providers": [],
                        "backchannel_providers_obj": [],
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
                        "backchannel_providers": [],
                        "backchannel_providers_obj": [],
                        "slug": "denied",
                    },
                ],
            },
        )
