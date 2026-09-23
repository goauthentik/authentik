"""authentik API Modelviewset tests"""

from collections.abc import Callable
from urllib.parse import urlencode

from django.test import TestCase
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.admin.api.version_history import VersionHistoryViewSet
from authentik.api.v3.urls import router
from authentik.core.tests.utils import RequestFactory, create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.tenants.api.domains import DomainViewSet
from authentik.tenants.api.tenants import TenantViewSet
from authentik.tenants.utils import get_current_tenant


class TestModelViewSets(TestCase):
    """Test Viewset"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.factory = RequestFactory()


def viewset_tester_factory(test_viewset: type[ModelViewSet], full=True) -> dict[str, Callable]:
    """Test Viewset"""

    def test_attrs(self: TestModelViewSets) -> None:
        """Test attributes we require on all viewsets"""
        self.assertIsNotNone(getattr(test_viewset, "ordering", None))
        self.assertIsNotNone(getattr(test_viewset, "search_fields", None))
        filterset_class = getattr(test_viewset, "filterset_class", None)
        if not filterset_class:
            self.assertIsNotNone(getattr(test_viewset, "filterset_fields", None))

    def test_ordering(self: TestModelViewSets) -> None:
        """Test that all ordering fields are correct"""
        view = test_viewset.as_view({"get": "list"})
        for ordering_field in test_viewset.ordering:
            with self.subTest(ordering_field):
                req = self.factory.get(
                    f"/?{urlencode({'ordering': ordering_field}, doseq=True)}", user=self.user
                )
                req.tenant = get_current_tenant()
                res = view(req)
                self.assertEqual(res.status_code, 200)

    def test_search(self: TestModelViewSets) -> None:
        """Test that search fields are correct"""
        view = test_viewset.as_view({"get": "list"})
        req = self.factory.get(
            f"/?{urlencode({'search': generate_id()}, doseq=True)}", user=self.user
        )
        req.tenant = get_current_tenant()
        res = view(req)
        self.assertEqual(res.status_code, 200)

    cases = {
        "attrs": test_attrs,
    }
    if full:
        cases["ordering"] = test_ordering
        cases["search"] = test_search
    return cases


for _, viewset, _ in router.registry:
    if not issubclass(viewset, ModelViewSet | ReadOnlyModelViewSet):
        continue
    full = viewset not in [VersionHistoryViewSet, DomainViewSet, TenantViewSet]
    for test, case in viewset_tester_factory(viewset, full=full).items():
        setattr(TestModelViewSets, f"test_viewset_{viewset.__name__}_{test}", case)
