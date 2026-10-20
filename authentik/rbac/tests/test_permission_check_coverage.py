"""Endpoints run the check functions they offer"""

from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from authentik.api.v3.urls import router
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.apps import EnableCustomPermissions
from authentik.rbac.endpoints import NARROW_LIST, Endpoints
from authentik.rbac.models import PermissionCheck, Role

DENY = "def has_permission(request):\n    return False"
FAIL_LIST = "def narrow_list(request, queryset):\n    raise ValueError"
FAIL_ALTER = "def alter_response(request, data):\n    raise ValueError"


class TestPermissionCheckCoverage(APITestCase):
    """Probe every list endpoint: a denying has_permission and a failing narrow_list
    must turn a visible list into a 403, and a failing alter_response into a 500."""

    def setUp(self):
        EnableCustomPermissions.set(True)

    def test_lists(self):
        user = create_test_user()
        role = Role.objects.create(name=generate_id())
        user.roles.add(role)
        self.client.force_login(user)
        viewsets = {prefix: viewset for prefix, viewset, basename in router.registry}
        check = PermissionCheck.objects.create(name=generate_id(), expression=DENY, endpoints=[])
        unreachable = []
        probed = []
        for endpoint in Endpoints.hookable().values():
            prefix, action = endpoint.id.rsplit(":", 1)
            model = getattr(getattr(viewsets.get(prefix), "queryset", None), "model", None)
            if action != "list" or model is None:
                continue
            role.assign_perms(f"{model._meta.app_label}.view_{model._meta.model_name}")
            url = f"/api/v3/{prefix}/"
            check.endpoints = []
            check.save()
            if self.client.get(url).status_code != HTTP_200_OK:
                unreachable.append(endpoint.id)
                continue
            probes = {DENY: 403, FAIL_ALTER: 500}
            if NARROW_LIST in endpoint.functions:
                probes[FAIL_LIST] = 403
            for expression, status in probes.items():
                check.expression = expression
                check.endpoints = [endpoint.id]
                check.save()
                response = self.client.get(url)
                self.assertEqual(response.status_code, status, (endpoint.id, expression))
            probed.append(endpoint.id)
        self.assertGreater(len(probed), 100, unreachable)
