"""Tests for shared HTTP caching of anonymous flow entry points."""

from http import HTTPStatus
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from authentik.brands.models import Brand
from authentik.core.tests.utils import create_test_brand, create_test_flow
from authentik.flows.models import FlowDesignation

_MODERN_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def vary_values(response) -> set[str]:
    """Return normalized Vary header values."""
    return {value.strip().lower() for value in response.get("Vary", "").split(",")}


class TestToDefaultFlowEdgeCache(TestCase):
    """Cache only redirects selected directly by the current brand."""

    def setUp(self):
        Brand.objects.all().delete()
        self.flow = create_test_flow(designation=FlowDesignation.AUTHENTICATION)
        self.brand = create_test_brand(flow_authentication=self.flow)
        self.url = reverse("authentik_flows:default-authentication")

    def test_explicit_brand_flow_is_publicly_cacheable(self):
        self.client.cookies.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn("public", response.get("Cache-Control", ""))
        self.assertIn("cookie", vary_values(response))

    def test_policy_selected_fallback_is_not_publicly_cacheable(self):
        self.brand.flow_authentication = None
        self.brand.save(update_fields=["flow_authentication"])
        self.client.cookies.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_session_request_is_not_publicly_cacheable(self):
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "some-opaque-token"
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_unrelated_cookie_is_not_publicly_cacheable(self):
        self.client.cookies["unrelated"] = "attacker-controlled-value"
        response = self.client.get(self.url)
        self.assertNotIn("public", response.get("Cache-Control", ""))


class TestFlowInterfaceViewEdgeCache(TestCase):
    """Cache only constrained variants of the anonymous flow shell."""

    def setUp(self):
        Brand.objects.all().delete()
        self.flow = create_test_flow(designation=FlowDesignation.AUTHENTICATION)
        create_test_brand(flow_authentication=self.flow)
        self.url = reverse("authentik_core:if-flow", kwargs={"flow_slug": self.flow.slug})

    def test_normal_anonymous_shell_is_publicly_cacheable(self):
        self.client.cookies.clear()
        response = self.client.get(self.url, HTTP_USER_AGENT=_MODERN_UA)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("public", response.get("Cache-Control", ""))
        self.assertTrue({"cookie", "accept-language", "user-agent"} <= vary_values(response))

    def test_cached_shell_omits_per_request_trace_metadata(self):
        self.client.cookies.clear()
        with patch(
            "authentik.brands.utils.get_http_meta",
            return_value={"sentry-trace": "request-specific-trace"},
        ):
            response = self.client.get(self.url, HTTP_USER_AGENT=_MODERN_UA)
        self.assertNotContains(response, "request-specific-trace")

    def test_session_request_is_not_publicly_cacheable(self):
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "some-opaque-token"
        response = self.client.get(self.url, HTTP_USER_AGENT=_MODERN_UA)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_inspector_is_not_publicly_cacheable(self):
        response = self.client.get(f"{self.url}?inspector", HTTP_USER_AGENT=_MODERN_UA)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_sfe_is_not_publicly_cacheable(self):
        response = self.client.get(f"{self.url}?sfe", HTTP_USER_AGENT=_MODERN_UA)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_legacy_user_agent_is_not_publicly_cacheable(self):
        user_agent = "Mozilla/5.0 (Trident/7.0; rv:11.0) like Gecko"
        response = self.client.get(self.url, HTTP_USER_AGENT=user_agent)
        self.assertNotIn("public", response.get("Cache-Control", ""))

    def test_generated_media_url_is_not_publicly_cacheable(self):
        self.flow.background = "managed-background.png"
        self.flow.save(update_fields=["background"])
        response = self.client.get(self.url, HTTP_USER_AGENT=_MODERN_UA)
        self.assertNotIn("public", response.get("Cache-Control", ""))
