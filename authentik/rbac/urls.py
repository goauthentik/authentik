from authentik.rbac.api.rbac import RBACPermissionViewSet
from authentik.rbac.api.rbac_roles import RoleAssignedPermissionViewSet
from authentik.rbac.api.rbac_users import UserAssignedPermissionViewSet
from authentik.rbac.api.roles import RoleViewSet

api_urlpatterns = [
    ("rbac/permissions", RBACPermissionViewSet),
    ("rbac/assigned_users", UserAssignedPermissionViewSet),
    ("rbac/assigned_roles", RoleAssignedPermissionViewSet),
    ("rbac/roles", RoleViewSet),
]
