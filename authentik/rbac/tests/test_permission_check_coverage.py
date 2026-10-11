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


class TestPermissionCheckCoverage(APITestCase):
    """Probe every list endpoint: a denying has_permission and a failing narrow_list
    must both turn a visible list into a 403."""

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
            probes = [DENY] + ([FAIL_LIST] if NARROW_LIST in endpoint.functions else [])
            for expression in probes:
                check.expression = expression
                check.endpoints = [endpoint.id]
                check.save()
                self.assertEqual(self.client.get(url).status_code, 403, (endpoint.id, expression))
            probed.append(endpoint.id)
        self.assertGreater(len(probed), 100, unreachable)
