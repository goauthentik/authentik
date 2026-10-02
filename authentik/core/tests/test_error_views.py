"""Test the views wired up as django's handler400/403/404/500"""

from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import create_test_brand
from authentik.core.views.error import (
    BadRequestView,
    ForbiddenView,
    NotFoundView,
    ServerErrorView,
)

HANDLERS = (
    (BadRequestView, 400),
    (ForbiddenView, 403),
    (NotFoundView, 404),
    (ServerErrorView, 500),
)
UNSAFE_METHODS = ("post", "put", "patch", "delete")


class TestErrorViews(TestCase):
    """The error handlers must answer with their own status code for every request
    method, not just GET.

    Django calls handler400/403/404/500 with the request that failed, whatever its
    method. A handler that only implements `get` answers a failing POST with 405
    Method Not Allowed and drops its own status code -- which made an error on a
    POST-only API endpoint surface to clients as `405`."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_get(self):
        """A GET keeps returning the handler's own status code"""
        for view, expected in HANDLERS:
            with self.subTest(view=view.__name__):
                response = view.as_view()(self.factory.get("/"))
                self.assertEqual(response.status_code, expected)

    def test_unsafe_methods(self):
        """A POST/PUT/PATCH/DELETE must not be answered with 405"""
        for view, expected in HANDLERS:
            for method in UNSAFE_METHODS:
                with self.subTest(view=view.__name__, method=method):
                    request = getattr(self.factory, method)("/")
                    response = view.as_view()(request)
                    self.assertEqual(response.status_code, expected)
                    self.assertNotIn("Allow", response)


class TestErrorViewsRouting(TestCase):
    """End-to-end: an unresolvable path must 404 regardless of request method.

    The DRF router matches a detail route's id with `[^/.]+`, so an id containing a
    dot never resolves and django raises Http404 before any view runs -- the
    "invalid ID" case that reported 405 rather than a descriptive error."""

    def setUp(self):
        create_test_brand()

    def test_unresolvable_api_path(self):
        """Every method gets 404, and the error page still renders"""
        url = "/api/v3/providers/scim/1.5/sync/object/"
        for method in ("get", *UNSAFE_METHODS):
            with self.subTest(method=method):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 404)
                self.assertTemplateUsed(response, "if/error.html")
