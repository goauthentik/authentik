"""RBAC API urls"""
from authentik.rbac.api.rbac import RBACPermissionViewSet
from authentik.rbac.api.rbac_assigned_by_roles import RoleAssignedPermissionViewSet
from authentik.rbac.api.rbac_assigned_by_users import UserAssignedPermissionViewSet
from authentik.rbac.api.rbac_roles import RolePermissionViewSet
from authentik.rbac.api.rbac_users import UserPermissionViewSet
from authentik.rbac.api.roles import RoleViewSet

api_urlpatterns = [
    (
        "rbac/permissions/assigned_by_users",
        UserAssignedPermissionViewSet,
        "permissions-assigned-by-users",
    ),
    (
        "rbac/permissions/assigned_by_roles",
        RoleAssignedPermissionViewSet,
        "permissions-assigned-by-roles",
    ),
    ("rbac/permissions/users", UserPermissionViewSet, "permissions-users"),
    ("rbac/permissions/roles", RolePermissionViewSet, "permissions-roles"),
    ("rbac/permissions", RBACPermissionViewSet),
    ("rbac/roles", RoleViewSet),
]
