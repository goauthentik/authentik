from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.events.models import Notification
from authentik.lib.generators import generate_id
from authentik.rbac.apps import EnableCustomPermissions
from authentik.rbac.models import PermissionCheck, Role

GRANTS = """
def has_permission(request):
    users = request.user._meta.model.objects.filter(username__startswith="grant-")
    granted = sum(request.user.has_perm("authentik_core.change_user", user) for user in users)
    if granted == int(request.query_params["expected"]):
        raise PermissionCheckSkipException()
    return False
"""


class TestRuntime(APITestCase):
    def setUp(self):
        EnableCustomPermissions.set(True)
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.user.roles.add(self.role)
        self.role.assign_perms("authentik_core.view_user")
        self.client.force_login(self.user)
        self.url = reverse("authentik_api:user-list")

    def bind(self, expression: str, *endpoints: str) -> PermissionCheck:
        return PermissionCheck.objects.create(
            name=generate_id(),
            expression=expression,
            endpoints=list(endpoints) or ["core/users:list"],
        )

    def test_disabled_runs_no_checks(self):
        self.bind("def has_permission(request):\n    return False")
        EnableCustomPermissions.set(False)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(any("authentik_rbac_permissioncheck" in query["sql"] for query in queries))

    def test_reason(self):
        self.bind(
            "def has_permission(request):\n"
            '    raise PermissionDenied("Administrators are managed by IT")'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Administrators are managed by IT")

    def test_grants_loaded_once(self):
        self.bind(GRANTS, "admin/system:get")
        # The first request of a test loads more than any later one
        self.client.get("/api/v3/admin/system/", {"expected": 0})
        queries = []
        for count, expected in ((4, 2), (16, 8)):
            existing = User.objects.filter(username__startswith="grant-").count()
            for index in range(existing, count):
                user = User.objects.create(username=f"grant-{index}-{generate_id()}")
                if index % 2:
                    self.role.assign_perms("authentik_core.change_user", user)
            with CaptureQueriesContext(connection) as captured:
                response = self.client.get("/api/v3/admin/system/", {"expected": expected})
            self.assertEqual(response.status_code, 200)
            queries.append(len(captured))
        self.assertEqual(queries[0], queries[1])

    def test_anonymous_requests_run_checks(self):
        self.bind('def has_permission(request):\n    raise PermissionDenied("Log in first")')
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Log in first")

    def test_granted_anonymous_requests_own_nothing(self):
        self.bind(
            "def has_permission(request):\n    raise PermissionCheckSkipException()",
            "events/notifications:list",
        )
        Notification.objects.create(user=self.user, body=generate_id())
        self.client.logout()
        response = self.client.get(reverse("authentik_api:notification-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_unknown_endpoints_reported(self):
        check = self.bind("def has_permission(request):\n    return True")
        PermissionCheck.objects.filter(pk=check.pk).update(
            endpoints=["core/users:list", "core/users:renamed"]
        )
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse("authentik_api:permissioncheck-detail", kwargs={"pk": check.pk})
        )
        self.assertEqual(response.json()["unknown_endpoints"], ["core/users:renamed"])
