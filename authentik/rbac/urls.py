"""RBAC API urls"""

from authentik.rbac.api.initial_permissions import InitialPermissionsViewSet
from authentik.rbac.api.rbac import RBACPermissionViewSet
from authentik.rbac.api.rbac_assigned_by_roles import RoleAssignedPermissionViewSet
from authentik.rbac.api.rbac_roles import RolePermissionViewSet
from authentik.rbac.api.roles import RoleViewSet

api_urlpatterns = [
    (
        "rbac/permissions/assigned_by_roles",
        RoleAssignedPermissionViewSet,
        "permissions-assigned-by-roles",
    ),
    ("rbac/permissions/roles", RolePermissionViewSet, "permissions-roles"),
    ("rbac/permissions", RBACPermissionViewSet),
    ("rbac/roles", RoleViewSet, "roles"),
    ("rbac/initial_permissions", InitialPermissionsViewSet, "initial-permissions"),
]
