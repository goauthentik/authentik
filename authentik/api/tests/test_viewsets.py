"""authentik API Modelviewset tests"""
from typing import Callable

from django.test import TestCase
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.api.v3.urls import router


class TestModelViewSets(TestCase):
    """Test Viewset"""


def viewset_tester_factory(test_viewset: type[ModelViewSet]) -> Callable:
    """Test Viewset"""

    def tester(self: TestModelViewSets):
        self.assertIsNotNone(getattr(test_viewset, "search_fields", None))
        self.assertIsNotNone(getattr(test_viewset, "ordering", None))
        filterset_class = getattr(test_viewset, "filterset_class", None)
        if not filterset_class:
            self.assertIsNotNone(getattr(test_viewset, "filterset_fields", None))

    return tester


for _, viewset, _ in router.registry:
    if not issubclass(viewset, (ModelViewSet, ReadOnlyModelViewSet)):
        continue
    setattr(TestModelViewSets, f"test_viewset_{viewset.__name__}", viewset_tester_factory(viewset))
