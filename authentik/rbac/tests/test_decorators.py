"""test decorators api"""

from guardian.shortcuts import assign_perm
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.viewsets import ModelViewSet

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import get_request
from authentik.rbac.decorators import permission_required


class MVS(ModelViewSet):

    queryset = Application.objects.all()
    lookup_field = "slug"

    @permission_required("authentik_core.view_application", ["authentik_events.view_event"])
    @action(detail=True, pagination_class=None, filter_backends=[])
    def test(self, request: Request, slug: str):
        self.get_object()
        return Response(status=200)


class TestAPIDecorators(APITestCase):
    """test decorators api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_user()

    def test_obj_perm_denied(self):
        """Test object perm denied"""
        request = get_request("", user=self.user)
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        response = MVS.as_view({"get": "test"})(request, slug=app.slug)
        self.assertEqual(response.status_code, 403)

    def test_obj_perm_global(self):
        """Test object perm successful (global)"""
        assign_perm("authentik_core.view_application", self.user)
        assign_perm("authentik_events.view_event", self.user)
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        request = get_request("", user=self.user)
        response = MVS.as_view({"get": "test"})(request, slug=app.slug)
        self.assertEqual(response.status_code, 200, response.data)

    def test_obj_perm_scoped(self):
        """Test object perm successful (scoped)"""
        assign_perm("authentik_events.view_event", self.user)
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        assign_perm("authentik_core.view_application", self.user, app)
        request = get_request("", user=self.user)
        response = MVS.as_view({"get": "test"})(request, slug=app.slug)
        self.assertEqual(response.status_code, 200)

    def test_other_perm_denied(self):
        """Test other perm denied"""
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        assign_perm("authentik_core.view_application", self.user, app)
        request = get_request("", user=self.user)
        response = MVS.as_view({"get": "test"})(request, slug=app.slug)
        self.assertEqual(response.status_code, 403)
