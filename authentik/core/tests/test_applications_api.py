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

#: What the serializer returns for an application nobody has configured.
#:
#: The column holds the model default — a bare list — which is read through the
#: backward-compatible branch of `ApplicationLinksSerializer.to_representation`,
#: so an untouched application reports the block turned off rather than failing.
EMPTY_APPLICATION_LINKS = {
    "enabled": False,
    "address": False,
    "title": "",
    "align": "center",
    "links": [],
}


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
                        "application_links": EMPTY_APPLICATION_LINKS,
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
                        "application_links": EMPTY_APPLICATION_LINKS,
                        "meta_publisher": "",
                        "policy_engine_mode": "any",
                    },
                    {
                        "launch_url": None,
                        "meta_description": "",
                        "meta_hide": False,
                        "application_links": EMPTY_APPLICATION_LINKS,
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

    def _patch_links(self, block):
        """PATCH the links block of `self.allowed` and return the response."""
        return self.client.patch(
            reverse("authentik_api:application-detail", kwargs={"slug": self.allowed.slug}),
            {"application_links": block},
            format="json",
        )

    def test_application_links_default(self):
        """Test the block reads as off for an application nobody configured"""
        self.client.force_login(self.user)
        slug = generate_id()
        response = self.client.post(
            reverse("authentik_api:application-list"),
            {"name": generate_id(), "slug": slug},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["application_links"], EMPTY_APPLICATION_LINKS)
        self.assertEqual(Application.objects.get(slug=slug).application_links, [])

    def test_application_links_set(self):
        """Test setting the whole block, and reading it back unchanged"""
        self.client.force_login(self.user)
        block = {
            "enabled": True,
            "address": True,
            "title": "Native clients",
            "align": "right",
            "links": [
                {"label": "App Store", "url": "https://example.com/app", "icon": "fa://fa-apple"},
                {"label": "Docs", "url": "http://example.com/docs", "icon": ""},
            ],
        }
        response = self._patch_links(block)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["application_links"], block)
        self.allowed.refresh_from_db()
        # Written by `ApplicationSerializer.update`, which sets the block aside
        # before delegating: a writable nested serializer is refused outright by
        # `ModelSerializer`, whatever the field it targets.
        self.assertEqual(self.allowed.application_links, block)

    def test_application_links_partial_block_fills_defaults(self):
        """Test an incomplete block is stored complete, not half-written"""
        self.client.force_login(self.user)
        response = self._patch_links({"enabled": True})
        self.assertEqual(response.status_code, 200)
        self.allowed.refresh_from_db()
        self.assertEqual(
            self.allowed.application_links,
            {"enabled": True, "address": False, "title": "", "align": "center", "links": []},
        )

    def test_application_links_legacy_list_is_read(self):
        """Test a bare list, the shape stored before the block gained settings

        Applications configured against the earlier version still hold a plain list
        in the column. Reading it must keep working without a data migration, and an
        administrator who had entered links meant them to show.
        """
        self.client.force_login(self.user)
        self.allowed.application_links = [{"label": "Docs", "url": "https://example.com"}]
        self.allowed.save()
        response = self.client.get(
            reverse("authentik_api:application-detail", kwargs={"slug": self.allowed.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["application_links"],
            {
                "enabled": True,
                "address": False,
                "title": "",
                "align": "center",
                "links": [{"label": "Docs", "url": "https://example.com", "icon": ""}],
            },
        )

    def test_application_links_icon_optional(self):
        """Test the icon of a link may be omitted"""
        self.client.force_login(self.user)
        response = self._patch_links(
            {"links": [{"label": "Docs", "url": "https://example.com/docs"}]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["application_links"]["links"][0]["icon"], "")

    def test_application_links_label_required(self):
        """Test a link without a label is rejected, on PATCH as well

        A nested serializer inherits `partial` from its root, so without an explicit
        guard a PATCH would skip the missing key rather than reject it.
        """
        self.client.force_login(self.user)
        response = self._patch_links({"links": [{"url": "https://example.com"}]})
        self.assertEqual(response.status_code, 400)
        self.assertIn("label", response.data["application_links"]["links"][0])

    def test_application_links_reject_unsafe_scheme(self):
        """Test link URLs are restricted to HTTP and HTTPS

        An administrator-supplied URL carrying a javascript: scheme would be stored
        XSS on an identity provider, so the check lives in the serializer and not
        only in the web component.
        """
        self.client.force_login(self.user)
        kept = {"enabled": True, "links": [{"label": "kept", "url": "https://example.com"}]}
        self.assertEqual(self._patch_links(kept).status_code, 200)
        self.allowed.refresh_from_db()
        stored = self.allowed.application_links
        for url in (
            "javascript:alert(1)",
            "JavaScript:alert(1)",
            "  javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd",
            "ftp://example.com/file",
        ):
            with self.subTest(url=url):
                response = self._patch_links({"links": [{"label": "unsafe", "url": url}]})
                self.assertEqual(response.status_code, 400)
                self.assertIn("url", response.data["application_links"]["links"][0])
        self.allowed.refresh_from_db()
        self.assertEqual(self.allowed.application_links, stored)

    def test_application_links_scheme_defaults_to_https(self):
        """Test a URL typed without a scheme is completed rather than refused

        `example.com` is what an administrator actually types. The value is
        unambiguous and HTTPS is the only sane reading of it, so refusing it would
        be a papercut with nothing behind it.
        """
        self.client.force_login(self.user)
        for typed, stored in (
            ("example.com", "https://example.com"),
            ("example.com/path?a=b", "https://example.com/path?a=b"),
            ("//example.com", "https://example.com"),
            ("  example.com  ", "https://example.com"),
            # Already carries a scheme: left exactly as it is.
            ("http://example.com", "http://example.com"),
            ("https://example.com", "https://example.com"),
        ):
            with self.subTest(typed=typed):
                response = self._patch_links({"links": [{"label": "Docs", "url": typed}]})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["application_links"]["links"][0]["url"], stored)

    def test_application_links_completion_does_not_rescue_a_bad_scheme(self):
        """Test completion never turns a refused scheme into an accepted URL

        This is what keeps the convenience above from becoming a hole: a value
        that already carries a scheme is never rewritten, so `javascript:` is
        rejected rather than becoming `https://javascript:alert(1)`.
        """
        self.client.force_login(self.user)
        response = self._patch_links({"links": [{"label": "XSS", "url": "javascript:alert(1)"}]})
        self.assertEqual(response.status_code, 400)
        self.assertIn("url", response.data["application_links"]["links"][0])

    def test_application_links_scheme_case_insensitive(self):
        """Test the scheme check does not depend on case"""
        self.client.force_login(self.user)
        response = self._patch_links(
            {"links": [{"label": "Docs", "url": "HTTPS://example.com/docs"}]}
        )
        self.assertEqual(response.status_code, 200)

    def test_application_links_reject_unknown_alignment(self):
        """Test the alignment is restricted to the three the stylesheet implements

        An unknown value would reach the card as a `data-align` no rule matches, and
        the heading would silently fall back to the browser default.
        """
        self.client.force_login(self.user)
        for align in ("start", "end", "justify", "middle", ""):
            with self.subTest(align=align):
                response = self._patch_links({"align": align})
                self.assertEqual(response.status_code, 400)
                self.assertIn("align", response.data["application_links"])

    def test_application_links_cleared(self):
        """Test the block can be emptied again"""
        self.client.force_login(self.user)
        self.allowed.application_links = {
            "enabled": True,
            "links": [{"label": "Docs", "url": "https://example.com"}],
        }
        self.allowed.save()
        response = self._patch_links({"enabled": False, "links": []})
        self.assertEqual(response.status_code, 200)
        self.allowed.refresh_from_db()
        self.assertEqual(self.allowed.application_links["links"], [])
        self.assertFalse(self.allowed.application_links["enabled"])
