"""Tests for HTTP edge-cache headers on the anonymous flow entry-point views.

Covers ``GET /flows/-/default/authentication/`` (``ToDefaultFlow.dispatch``)
and ``GET /if/flow/<slug>/`` (``FlowInterfaceView.dispatch``).
"""

from http import HTTPStatus

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from authentik.brands.models import Brand
from authentik.core.tests.utils import create_test_brand, create_test_flow
from authentik.flows.models import FlowDesignation
from authentik.lib.http_cache import (
    ANONYMOUS_ROOT_REDIRECT_CACHE_SECONDS,
    anonymous_redirect_cache_control,
)

_MODERN_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class TestToDefaultFlowEdgeCache(TestCase):
    """``/flows/-/default/authentication/`` must be edge-cacheable for
    anonymous, cookieless visitors."""

    def setUp(self):
        Brand.objects.all().delete()
        self.flow = create_test_flow(designation=FlowDesignation.AUTHENTICATION)
        self.brand = create_test_brand(flow_authentication=self.flow)

    def test_anonymous_no_cookie_is_publicly_cacheable(self):
        """No session cookie → 302 with publicly cacheable headers."""
        self.client.cookies.clear()
        response = self.client.get(reverse("authentik_flows:default-authentication"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            response["Cache-Control"],
            anonymous_redirect_cache_control(),
        )

    def test_anonymous_no_cookie_response_blocks_browser_cache(self):
        """``max-age=0`` prevents browser caching (post-login loop guard);
        ``s-maxage`` keeps shared-cache caching."""
        self.client.cookies.clear()
        response = self.client.get(reverse("authentik_flows:default-authentication"))
        cache_control = response.get("Cache-Control", "")
        self.assertIn("max-age=0", cache_control)
        self.assertIn(f"s-maxage={ANONYMOUS_ROOT_REDIRECT_CACHE_SECONDS}", cache_control)

    def test_anonymous_no_cookie_response_has_no_vary_cookie(self):
        """Cookieless publicly-cacheable responses must not carry
        ``Vary: Cookie`` — otherwise shared caches refuse to serve them."""
        self.client.cookies.clear()
        response = self.client.get(reverse("authentik_flows:default-authentication"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn("public", response.get("Cache-Control", ""))
        vary_values = [v.strip().lower() for v in response.get("Vary", "").split(",")]
        self.assertNotIn("cookie", vary_values)

    def test_anonymous_with_cookie_is_not_publicly_cacheable(self):
        """A request with a session cookie does not get
        ``Cache-Control: public`` — the response could vary by session state."""
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "some-opaque-token"
        response = self.client.get(reverse("authentik_flows:default-authentication"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_invalidation_endpoint_also_cacheable_for_anonymous(self):
        """``/flows/-/default/invalidation/`` uses the same view and should
        carry the same cache header on anonymous cookieless requests."""
        create_test_flow(designation=FlowDesignation.INVALIDATION)
        self.brand.refresh_from_db()
        self.client.cookies.clear()
        response = self.client.get(reverse("authentik_flows:default-invalidation"))
        if response.status_code == HTTPStatus.FOUND:
            self.assertEqual(
                response["Cache-Control"],
                anonymous_redirect_cache_control(),
            )


class TestFlowInterfaceViewEdgeCache(TestCase):
    """``/if/flow/<slug>/`` must be edge-cacheable for the common
    modern-browser, anonymous, cookieless case. Variant-producing query
    params and SFE-routed UAs must opt out."""

    def setUp(self):
        Brand.objects.all().delete()
        self.flow = create_test_flow(designation=FlowDesignation.AUTHENTICATION)
        self.brand = create_test_brand(flow_authentication=self.flow)

    def _url(self) -> str:
        return reverse("authentik_core:if-flow", kwargs={"flow_slug": self.flow.slug})

    def test_anonymous_modern_browser_is_publicly_cacheable(self):
        """Anonymous, no cookie, modern UA → publicly cacheable."""
        self.client.cookies.clear()
        response = self.client.get(self._url(), HTTP_USER_AGENT=_MODERN_UA)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response["Cache-Control"],
            anonymous_redirect_cache_control(),
        )

    def test_anonymous_modern_browser_response_blocks_browser_cache(self):
        """``max-age=0`` prevents browser caching of the HTML page."""
        self.client.cookies.clear()
        response = self.client.get(self._url(), HTTP_USER_AGENT=_MODERN_UA)
        cache_control = response.get("Cache-Control", "")
        self.assertIn("max-age=0", cache_control)
        self.assertIn(f"s-maxage={ANONYMOUS_ROOT_REDIRECT_CACHE_SECONDS}", cache_control)

    def test_anonymous_modern_browser_response_has_no_vary_cookie(self):
        """Cookieless cacheable responses must not carry ``Vary: Cookie``."""
        self.client.cookies.clear()
        response = self.client.get(self._url(), HTTP_USER_AGENT=_MODERN_UA)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("public", response.get("Cache-Control", ""))
        vary_values = [v.strip().lower() for v in response.get("Vary", "").split(",")]
        self.assertNotIn("cookie", vary_values)

    def test_anonymous_with_cookie_is_not_publicly_cacheable(self):
        """Cookie present → never publicly cacheable, even if anonymous."""
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "some-opaque-token"
        response = self.client.get(self._url(), HTTP_USER_AGENT=_MODERN_UA)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_inspector_query_param_disables_caching(self):
        """``?inspector`` produces a different template variant; not cacheable."""
        self.client.cookies.clear()
        response = self.client.get(self._url() + "?inspector", HTTP_USER_AGENT=_MODERN_UA)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_sfe_query_param_disables_caching(self):
        """``?sfe`` forces the SFE template; not cacheable."""
        self.client.cookies.clear()
        response = self.client.get(self._url() + "?sfe", HTTP_USER_AGENT=_MODERN_UA)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_ie_user_agent_disables_caching(self):
        """IE UAs route to the SFE template via ``compat_needs_sfe``; not cacheable."""
        self.client.cookies.clear()
        ie_ua = "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
        response = self.client.get(self._url(), HTTP_USER_AGENT=ie_ua)
        self.assertNotIn("public", response.get("Cache-Control", ""))
