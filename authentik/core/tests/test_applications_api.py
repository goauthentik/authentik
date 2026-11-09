"""Test Applications API"""

from json import loads
from unittest.mock import patch

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APITestCase

from authentik.core.models import Application, PropertyMapping
from authentik.core.tests.utils import (
    create_test_admin_user,
    create_test_flow,
    create_test_user,
)
from authentik.flows.signals import delete_cache_prefix
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.policies.types import CACHE_PREFIX
from authentik.providers.ldap.models import LDAPProvider
from authentik.providers.oauth2.models import OAuth2Provider, RedirectURI, RedirectURIMatchingMode
from authentik.providers.proxy.models import ProxyProvider
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.scim.models import SCIMProvider


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

    def test_formatted_launch_url_percent_encoding(self):
        """Only placeholders and `%%` are formatted, percent-encoding is kept as is rather than
        being filled with the whole user"""
        self.allowed.meta_launch_url = "https://goauthentik.io/%(username)s/Joe%27s?q=a%20b%%2F%"
        self.assertEqual(
            self.allowed.get_launch_url(self.user),
            f"https://goauthentik.io/{self.user.username}/Joe%27s?q=a%20b%2F%",
        )
        self.allowed.meta_launch_url = "https://goauthentik.io/Joe%27s"
        self.assertEqual(self.allowed.get_launch_url(self.user), "https://goauthentik.io/Joe%27s")

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

    def test_list_accessible(self):
        """Test listing applications the user passes policies for"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentik_api:application-accessible"))
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
                        "pbm_uuid": str(self.allowed.pbm_uuid),
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
                        "meta_hide": False,
                        "meta_publisher": "",
                        "policy_engine_mode": "any",
                    },
                ],
            },
        )

    def test_list_rbac(self):
        """Test listing applications the user has RBAC permissions for"""
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
                        "pbm_uuid": str(self.allowed.pbm_uuid),
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
                        "meta_hide": False,
                        "meta_publisher": "",
                        "policy_engine_mode": "any",
                    },
                    {
                        "launch_url": None,
                        "meta_description": "",
                        "meta_hide": False,
                        "meta_icon": "",
                        "meta_icon_url": None,
                        "meta_icon_themed_urls": None,
                        "meta_launch_url": "",
                        "open_in_new_tab": False,
                        "meta_publisher": "",
                        "group": "",
                        "name": "denied",
                        "pbm_uuid": str(self.denied.pbm_uuid),
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

    def test_list_plain_launch_url(self):
        """A launch URL without placeholders is not formatted, so listing it does not serialize
        the requesting user, whose avatar lookup can make an HTTP request"""
        self.allowed.meta_launch_url = "https://goauthentik.io"
        self.allowed.save()
        self.client.force_login(self.user)
        with patch("authentik.core.api.users.get_avatar") as get_avatar:
            response = self.client.get(reverse("authentik_api:application-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["launch_url"], "https://goauthentik.io")
        get_avatar.assert_not_called()

    def test_update_provider(self):
        """Changing an application's provider returns the new provider"""
        self.client.force_login(self.user)
        url = reverse("authentik_api:application-detail", kwargs={"slug": self.allowed.slug})
        provider = SAMLProvider.objects.create(name=generate_id())
        response = self.client.patch(url, {"provider": provider.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider_obj"]["pk"], provider.pk)
        self.assertEqual(response.json()["provider_obj"]["component"], "ak-provider-saml-form")
        response = self.client.patch(url, {"provider": None}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["provider_obj"])

    def test_with_provider_combined(self):
        """with_provider() can be called again, and after lookups through the provider"""
        provider = SAMLProvider.objects.create(name=generate_id())
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        app = (
            Application.objects.prefetch_related("provider__property_mappings")
            .with_provider()
            .with_provider()
            .get(pk=app.pk)
        )
        with self.assertNumQueries(0):
            self.assertEqual(app.get_provider(), provider)
            self.assertEqual(list(app.get_provider().property_mappings.all()), [])

    def test_list_rbac_ignores_policies(self):
        """RBAC access and policy access are separate: the list only checks
        permissions, @accessible only checks policies"""
        user = create_test_user()
        user.assign_perms_to_managed_role("authentik_core.view_application", self.denied)
        self.client.force_login(user)
        response = self.client.get(reverse("authentik_api:application-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([app["slug"] for app in response.json()["results"]], [self.denied.slug])
        response = self.client.get(reverse("authentik_api:application-accessible"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([app["slug"] for app in response.json()["results"]], [self.allowed.slug])

    def test_list_accessible_for_user(self):
        """for_user requires the view_user_applications permission on that user"""
        user = create_test_user()
        PolicyBinding.objects.create(target=self.allowed, user=user, order=0)
        url = reverse("authentik_api:application-accessible") + f"?for_user={user.pk}"
        self.client.force_login(create_test_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([app["slug"] for app in response.json()["results"]], [self.allowed.slug])
        self.assertEqual(
            response.json()["results"][0]["launch_url"], f"https://goauthentik.io/{user.username}"
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

    def _create_applications(self, count: int, allowed_user, denied_user) -> list[Application]:
        """Applications with each provider type and a backchannel provider, every other one
        bound to `allowed_user` and the rest to `denied_user`"""
        flow = create_test_flow()
        mapping = PropertyMapping.objects.create(name=generate_id(), expression="return {}")
        apps = []
        for index in range(count):
            model = (OAuth2Provider, SAMLProvider, ProxyProvider, LDAPProvider)[index % 4]
            provider = model.objects.create(name=generate_id(), authorization_flow=flow)
            provider.property_mappings.add(mapping)
            app = Application.objects.create(
                name=generate_id(),
                slug=generate_id(),
                provider=provider,
                meta_launch_url="https://goauthentik.io",
            )
            backchannel = SCIMProvider.objects.create(
                name=generate_id(), url="https://goauthentik.io", token=generate_id()
            )
            backchannel.property_mappings.add(mapping)
            app.backchannel_providers.add(backchannel)
            PolicyBinding.objects.create(
                target=app, user=allowed_user if index % 2 else denied_user, order=0
            )
            apps.append(app)
        return apps

    def _get_queries(self, url: str, cached=False) -> tuple[Response, CaptureQueriesContext]:
        """Request `url` twice and capture the queries of the second request, as the first one
        after a change also loads the session and brand. Unless `cached`, both requests evaluate
        policies; with it, the second request reads the user's application list that the first
        one cached."""
        delete_cache_prefix(f"{CACHE_PREFIX}*")
        self.assertEqual(self.client.get(url).status_code, 200)
        if not cached:
            delete_cache_prefix(f"{CACHE_PREFIX}*")
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response, captured

    def _assert_serialized(self, results: list[dict], apps: list[Application]):
        """`results` are exactly `apps`, with providers serialized as their concrete type and
        with their applications"""
        by_slug = {app["slug"]: app for app in results}
        self.assertCountEqual(by_slug, [app.slug for app in apps])
        for app in apps:
            provider = app.provider
            backchannel = SCIMProvider.objects.get(backchannel_application=app)
            data = by_slug[app.slug]
            self.assertEqual(data["provider_obj"]["component"], provider.component)
            self.assertEqual(data["provider_obj"]["assigned_application_slug"], app.slug)
            self.assertEqual(
                data["provider_obj"]["property_mappings"],
                [str(pk) for pk in provider.property_mappings.values_list("pk", flat=True)],
            )
            self.assertEqual(data["backchannel_providers"], [backchannel.pk])
            self.assertEqual(len(data["backchannel_providers_obj"]), 1)
            self.assertEqual(
                data["backchannel_providers_obj"][0]["component"], backchannel.component
            )
            self.assertEqual(
                data["backchannel_providers_obj"][0]["assigned_backchannel_application_slug"],
                app.slug,
            )
            self.assertIsNone(data["backchannel_providers_obj"][0]["assigned_application_slug"])
            self.assertEqual(
                data["backchannel_providers_obj"][0]["property_mappings"],
                [str(pk) for pk in backchannel.property_mappings.values_list("pk", flat=True)],
            )

    def test_list_queries(self):
        """Listing applications loads providers in their own queries: joining every provider
        subclass into the application query made a statement Postgres took over 100ms to plan.
        The number of queries does not grow with the number of applications."""
        Application.objects.all().delete()
        denied_user = create_test_user()
        apps = self._create_applications(4, self.user, denied_user)
        self.client.force_login(self.user)
        url = reverse("authentik_api:application-list")
        response, small = self._get_queries(url)
        for query in small.captured_queries:
            sql = query["sql"]
            self.assertFalse(
                'FROM "authentik_core_application"' in sql and "authentik_core_provider" in sql,
                "The application query joins providers",
            )
        self._assert_serialized(response.json()["results"], apps)

        apps += self._create_applications(8, self.user, denied_user)
        response, large = self._get_queries(url)
        self._assert_serialized(response.json()["results"], apps)
        self.assertEqual(len(large), len(small))

    def test_list_accessible_queries(self):
        """@accessible returns exactly the applications whose policies the user passes, whether
        it evaluates policies or reads the user's application list from the cache, and the number
        of queries does not grow with the number of applications."""
        Application.objects.all().delete()
        user = create_test_user()
        allowed = self._create_applications(4, user, self.user)[1::2]
        self.client.force_login(user)
        url = reverse("authentik_api:application-accessible") + "?only_with_launch_url=true"
        small = {}
        for cached in (False, True):
            response, small[cached] = self._get_queries(url, cached)
            self._assert_serialized(response.json()["results"], allowed)

        allowed += self._create_applications(8, user, self.user)[1::2]
        for cached in (False, True):
            response, large = self._get_queries(url, cached)
            self._assert_serialized(response.json()["results"], allowed)
            self.assertEqual(len(large), len(small[cached]))
