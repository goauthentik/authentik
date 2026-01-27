"""Test Applications API"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import OAuth2Provider, RedirectURI, RedirectURIMatchingMode
from authentik.providers.proxy.models import ProxyProvider
from authentik.providers.saml.models import SAMLProvider


class TestApplicationsAPI(APITestCase):
    """Test applications API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.provider = OAuth2Provider.objects.create(
            name="test",
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://some-other-domain")],
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
                        "name": "allowed",
                        "slug": "allowed",
                        "group": "",
                        "provider": self.provider.pk,
                        "provider_obj": {
                            "assigned_application_name": "allowed",
                            "assigned_application_slug": "allowed",
                            "assigned_backchannel_application_name": None,
                            "assigned_backchannel_application_slug": None,
                            "authentication_flow": None,
                            "invalidation_flow": None,
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
                        "meta_icon": "",
                        "meta_icon_url": None,
                        "meta_icon_themed_urls": None,
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
                        "name": "allowed",
                        "slug": "allowed",
                        "group": "",
                        "provider": self.provider.pk,
                        "provider_obj": {
                            "assigned_application_name": "allowed",
                            "assigned_application_slug": "allowed",
                            "assigned_backchannel_application_name": None,
                            "assigned_backchannel_application_slug": None,
                            "authentication_flow": None,
                            "invalidation_flow": None,
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
                        "meta_icon": "",
                        "meta_icon_url": None,
                        "meta_icon_themed_urls": None,
                        "meta_description": "",
                        "meta_publisher": "",
                        "policy_engine_mode": "any",
                    },
                    {
                        "launch_url": None,
                        "meta_description": "",
                        "meta_icon": "",
                        "meta_icon_url": None,
                        "meta_icon_themed_urls": None,
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

    def test_get_provider(self):
        """Ensure that proxy providers (at the time of writing that is the only provider
        that inherits from another proxy type (OAuth) instead of inheriting from the root
        provider class) is correctly looked up and selected from the database"""
        slug = generate_id()
        provider = ProxyProvider.objects.create(name=generate_id())
        Application.objects.create(
            name=generate_id(),
            slug=slug,
            provider=provider,
        )
        self.assertEqual(Application.objects.get(slug=slug).get_provider(), provider)
        self.assertEqual(
            Application.objects.with_provider().get(slug=slug).get_provider(), provider
        )

        slug = generate_id()
        provider = SAMLProvider.objects.create(name=generate_id())
        Application.objects.create(
            name=generate_id(),
            slug=slug,
            provider=provider,
        )
        self.assertEqual(Application.objects.get(slug=slug).get_provider(), provider)
        self.assertEqual(
            Application.objects.with_provider().get(slug=slug).get_provider(), provider
        )

    def test_create_application_with_reserved_slug(self):
        """Test creating an application with a reserved slug"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:application-list"),
            {
                "name": "Test Application",
                "slug": Application.reserved_slugs[0],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)
        self.assertIn("reserved", response.data["slug"][0])

    def test_update_application_with_reserved_slug(self):
        """Test updating an application to use a reserved slug"""
        self.client.force_login(self.user)
        app = Application.objects.create(
            name="Test Application",
            slug="valid-slug",
        )

        response = self.client.patch(
            reverse("authentik_api:application-detail", kwargs={"slug": app.slug}),
            {
                "slug": Application.reserved_slugs[0],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)
        self.assertIn("reserved", response.data["slug"][0])
