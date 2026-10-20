"""Test hot URL ordering"""

from django.test import SimpleTestCase
from django.urls import include, path, resolve, reverse
from django.views import View

from authentik.api.v3.urls import urlpatterns
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.utils.urls import hot_path, sort_hot


class TestURLs(SimpleTestCase):
    """Test hot URL ordering"""

    def test_hot_sorted_first(self):
        """Hot patterns come before all other patterns and still resolve"""
        hot = [isinstance(pattern, hot_path) for pattern in urlpatterns]
        self.assertTrue(hot[0])
        self.assertEqual(hot, sorted(hot, reverse=True))
        match = resolve(reverse("authentik_api:flow-executor", kwargs={"flow_slug": "foo"}))
        self.assertEqual(match.func.view_class, FlowExecutorView)

    def test_hot_include(self):
        """Includes containing a hot pattern are sorted before other patterns"""
        cold = path("a/", View.as_view())
        cold_include = path("b/", include([path("c/", View.as_view())]))
        hot_include = path("", include([hot_path("d/", View.as_view())]))
        self.assertEqual(
            sort_hot([cold, cold_include, hot_include]), [hot_include, cold, cold_include]
        )
