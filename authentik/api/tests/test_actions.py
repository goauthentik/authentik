from collections.abc import Callable
from inspect import getmembers

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.viewsets import GenericViewSet

from authentik.lib.utils.reflection import all_subclasses


class TestActionDecoratorAPI(APITestCase): ...


def api_viewset_action(viewset: GenericViewSet, member: Callable) -> Callable:
    """Test API Viewset action"""

    def tester(self: TestActionDecoratorAPI):
        if "permission_classes" in member.kwargs:
            self.assertNotEqual(member.kwargs["permission_classes"], [])
        if "authentication_classes" in member.kwargs:
            self.assertNotEqual(member.kwargs["authentication_classes"], [])

    return tester

# Tell django to load all URLs
reverse("authentik_core:root-redirect")
for viewset in all_subclasses(GenericViewSet):
    for act_name, member in getmembers(viewset(), lambda x: isinstance(x, Callable)):
        if not hasattr(member, "kwargs") or not hasattr(member, "mapping"):
            continue
        setattr(
            TestActionDecoratorAPI,
            f"test_viewset_{viewset.__name__}_action_{act_name}",
            api_viewset_action(viewset, member),
        )
