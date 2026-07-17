"""Test interface view redirect behavior by user type"""

from http import HTTPStatus

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from authentik.brands.models import Brand
from authentik.core.apps import Setup
from authentik.core.models import Application, UserTypes
from authentik.core.tests.utils import create_test_brand, create_test_user
from authentik.core.views.interface import (
    ANONYMOUS_ROOT_REDIRECT_CACHE_SECONDS,
    anonymous_redirect_cache_control,
)


class TestInterfaceRedirects(TestCase):
    """Test RootRedirectView and BrandDefaultRedirectView redirect logic by user type"""

    def setUp(self):
        Setup.set(True)
        self.app = Application.objects.create(name="test-app", slug="test-app")
        self.brand: Brand = create_test_brand(default_application=self.app)

    def _assert_redirects_to_app(self, url_name: str, user_type: UserTypes):
        user = create_test_user(type=user_type)
        self.client.force_login(user)
        response = self.client.get(reverse(f"authentik_core:{url_name}"))
        self.assertRedirects(
            response,
            reverse(
                "authentik_core:application-launch", kwargs={"application_slug": self.app.slug}
            ),
            fetch_redirect_response=False,
        )

    def _assert_no_redirect(self, url_name: str, user_type: UserTypes):
        """Internal users should not be redirected away."""
        user = create_test_user(type=user_type)
        self.client.force_login(user)
        response = self.client.get(reverse(f"authentik_core:{url_name}"))
        # Internal users get a 200 (rendered template) or redirect to if-user, not to the app
        app_url = reverse(
            "authentik_core:application-launch", kwargs={"application_slug": self.app.slug}
        )
        self.assertNotEqual(response.get("Location"), app_url)

    # --- RootRedirectView ---

    def test_root_redirect_external_user(self):
        """External users are redirected to the default app from root"""
        self._assert_redirects_to_app("root-redirect", UserTypes.EXTERNAL)

    def test_root_redirect_service_account(self):
        """Service accounts are redirected to the default app from root"""
        self._assert_redirects_to_app("root-redirect", UserTypes.SERVICE_ACCOUNT)

    def test_root_redirect_internal_service_account(self):
        """Internal service accounts are redirected to the default app from root"""
        self._assert_redirects_to_app("root-redirect", UserTypes.INTERNAL_SERVICE_ACCOUNT)

    def test_root_redirect_internal_user(self):
        """Internal users are NOT redirected to the app from root"""
        self._assert_no_redirect("root-redirect", UserTypes.INTERNAL)

    # --- BrandDefaultRedirectView (if/user/) ---

    def test_if_user_external_user(self):
        """External users are redirected to the default app from if/user/"""
        self._assert_redirects_to_app("if-user", UserTypes.EXTERNAL)

    def test_if_user_service_account(self):
        """Service accounts are redirected to the default app from if/user/"""
        self._assert_redirects_to_app("if-user", UserTypes.SERVICE_ACCOUNT)

    def test_if_user_internal_service_account(self):
        """Internal service accounts are redirected to the default app from if/user/"""
        self._assert_redirects_to_app("if-user", UserTypes.INTERNAL_SERVICE_ACCOUNT)

    def test_if_user_internal_user(self):
        """Internal users are NOT redirected to the app from if/user/"""
        self._assert_no_redirect("if-user", UserTypes.INTERNAL)

    # --- BrandDefaultRedirectView (if/admin/) ---

    def test_if_admin_service_account(self):
        """Service accounts are redirected to the default app from if/admin/"""
        self._assert_redirects_to_app("if-admin", UserTypes.SERVICE_ACCOUNT)

    def test_if_admin_internal_service_account(self):
        """Internal service accounts are redirected to the default app from if/admin/"""
        self._assert_redirects_to_app("if-admin", UserTypes.INTERNAL_SERVICE_ACCOUNT)

    def test_if_admin_internal_user(self):
        """Internal users are NOT redirected to the app from if/admin/"""
        self._assert_no_redirect("if-admin", UserTypes.INTERNAL)

    # --- No default app set ---

    def test_service_account_no_default_app_access_denied(self):
        """Service accounts get access denied when no default app is configured"""
        self.brand.default_application = None
        self.brand.save()
        user = create_test_user(type=UserTypes.SERVICE_ACCOUNT)
        self.client.force_login(user)
        response = self.client.get(reverse("authentik_core:if-user"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Interface can only be accessed by internal users", response.content)

    # --- Anonymous root redirect HTTP caching ---

    def test_root_anonymous_no_cookie_is_publicly_cacheable(self):
        """Cookieless ``GET /`` returns 302 with publicly cacheable headers."""
        self.client.cookies.clear()
        response = self.client.get(reverse("authentik_core:root-redirect"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            response["Cache-Control"],
            anonymous_redirect_cache_control(),
        )

    def test_root_anonymous_no_cookie_response_blocks_browser_cache(self):
        """``Cache-Control`` carries ``max-age=0`` so browsers don't cache —
        prevents the post-login redirect loop. ``s-maxage`` keeps CDN caching."""
        self.client.cookies.clear()
        response = self.client.get(reverse("authentik_core:root-redirect"))
        cache_control = response.get("Cache-Control", "")
        self.assertIn("max-age=0", cache_control)
        self.assertIn(f"s-maxage={ANONYMOUS_ROOT_REDIRECT_CACHE_SECONDS}", cache_control)

    def test_root_anonymous_no_cookie_response_has_no_vary_cookie(self):
        """Cookieless publicly-cacheable responses must not carry
        ``Vary: Cookie`` — otherwise shared caches refuse to serve them."""
        self.client.cookies.clear()
        response = self.client.get(reverse("authentik_core:root-redirect"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn("public", response.get("Cache-Control", ""))
        vary_values = [v.strip().lower() for v in response.get("Vary", "").split(",")]
        self.assertNotIn("cookie", vary_values)

    def test_root_anonymous_with_cookie_is_not_publicly_cacheable(self):
        """A request with a session cookie does not get
        ``Cache-Control: public`` — it's potentially per-user."""
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "some-opaque-token"
        response = self.client.get(reverse("authentik_core:root-redirect"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertNotIn("public", response.get("Cache-Control", ""))
