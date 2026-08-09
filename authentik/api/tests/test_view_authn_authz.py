from collections.abc import Callable
from inspect import getmembers

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from authentik.lib.utils.reflection import all_subclasses


class TestAPIViewAuthnAuthz(APITestCase): ...


def api_viewset_action(viewset: GenericViewSet, member: Callable) -> Callable:
    """Test API Viewset action"""

    def tester(self: TestAPIViewAuthnAuthz):
        if "permission_classes" in member.kwargs:
            self.assertNotEqual(
                member.kwargs["permission_classes"], [], "permission_classes should not be empty"
            )
        if "authentication_classes" in member.kwargs:
            self.assertNotEqual(
                member.kwargs["authentication_classes"],
                [],
                "authentication_classes should not be empty",
            )

    return tester


def api_view(view: APIView) -> Callable:

    def tester(self: TestAPIViewAuthnAuthz):
        self.assertNotEqual(view.permission_classes, [], "permission_classes should not be empty")
        self.assertNotEqual(
            view.authentication_classes,
            [],
            "authentication_classes should not be empty",
        )

    return tester


# Tell django to load all URLs
reverse("authentik_core:root-redirect")
for viewset in all_subclasses(GenericViewSet):
    for act_name, member in getmembers(viewset(), lambda x: isinstance(x, Callable)):
        if not hasattr(member, "kwargs") or not hasattr(member, "mapping"):
            continue
        setattr(
            TestAPIViewAuthnAuthz,
            f"test_viewset_{viewset.__name__}_action_{act_name}",
            api_viewset_action(viewset, member),
        )
for view in all_subclasses(APIView):
    setattr(
        TestAPIViewAuthnAuthz,
        f"test_view_{view.__name__}",
        api_view(view),
    )
