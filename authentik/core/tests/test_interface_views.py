"""Test interface view redirect behavior by user type"""

from django.test import TestCase
from django.urls import resolve, reverse

from authentik.brands.models import Brand
from authentik.core.apps import Setup
from authentik.core.models import Application, UserTypes
from authentik.core.tests.utils import create_test_brand, create_test_user
from authentik.lib.config import CONFIG


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


class TestInterfaceCatchAll(TestCase):
    """Path-based routing: any subpath under if/admin/ and if/user/ renders the SPA shell."""

    def setUp(self):
        Setup.set(True)
        self.user = create_test_user(type=UserTypes.INTERNAL)
        create_test_brand()
        self.client.force_login(self.user)

    def test_admin_exact_prefix_renders_shell(self):
        """The exact /if/admin/ prefix still renders the admin interface."""
        response = self.client.get(reverse("authentik_core:if-admin"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "if/admin.html")
        self.assertIn(b"ak-interface-admin", response.content)

    def test_user_exact_prefix_renders_shell(self):
        """The exact /if/user/ prefix still renders the user interface."""
        response = self.client.get(reverse("authentik_core:if-user"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "if/user.html")
        self.assertIn(b"ak-interface-user", response.content)

    def test_admin_deep_subpath_renders_shell(self):
        """An arbitrary nested admin path returns the admin shell, not a 404."""
        response = self.client.get("/if/admin/identity/users/42")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "if/admin.html")
        self.assertIn(b"ak-interface-admin", response.content)

    def test_user_deep_subpath_renders_shell(self):
        """An arbitrary nested user path returns the user shell, not a 404."""
        response = self.client.get("/if/user/settings/sources")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "if/user.html")
        self.assertIn(b"ak-interface-user", response.content)

    def test_admin_subpath_is_reversible(self):
        """The admin catch-all route reverses with a path kwarg."""
        self.assertEqual(
            reverse("authentik_core:if-admin-path", kwargs={"path": "flow/inspector"}),
            "/if/admin/flow/inspector",
        )

    def test_user_subpath_is_reversible(self):
        """The user catch-all route reverses with a path kwarg."""
        self.assertEqual(
            reverse("authentik_core:if-user-path", kwargs={"path": "settings"}),
            "/if/user/settings",
        )

    def test_deep_subpath_carries_interface_context(self):
        """The deep-path shell carries the same injected config as the root."""
        response = self.client.get("/if/admin/core/applications")
        self.assertEqual(response.status_code, 200)
        # base/header_js.html injects window.authentik from the InterfaceView context.
        self.assertIn(b"window.authentik", response.content)
        self.assertIn(b'relBase: "/"', response.content)

    def test_exact_admin_prefix_not_shadowed_by_catchall(self):
        """Ordering: the exact route wins over the catch-all for /if/admin/."""
        self.assertEqual(resolve("/if/admin/").url_name, "if-admin")

    def test_exact_user_prefix_not_shadowed_by_catchall(self):
        """Ordering: the exact route wins over the catch-all for /if/user/."""
        self.assertEqual(resolve("/if/user/").url_name, "if-user")

    def test_flow_route_not_shadowed(self):
        """The catch-alls must not swallow flow URLs."""
        self.assertEqual(resolve("/if/flow/some-slug/").url_name, "if-flow")

    def test_ws_client_route_not_shadowed(self):
        """The catch-alls must not swallow the websocket fallback URL."""
        self.assertNotIn(resolve("/ws/client/").url_name, ("if-admin-path", "if-user-path"))

    def test_api_route_not_shadowed(self):
        """The catch-alls live under core's urlconf and must not affect the API."""
        self.assertNotIn(resolve("/api/v3/core/users/").url_name, ("if-admin-path", "if-user-path"))

    def test_web_path_reflected_in_shell_context(self):
        """When web.path is non-root, the shell advertises it via relBase.

        Routing under web.path is resolved at import time in the root urlconf, so
        only the request-time context value is exercised here; deployment-prefix
        routing is covered by the Playwright web.path smoke test in a later PR.
        """
        with CONFIG.patch("web.path", "/auth/"):
            response = self.client.get("/if/user/settings")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'relBase: "/auth/"', response.content)
