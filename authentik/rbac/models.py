"""RBAC models"""

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from django.contrib.auth.models import Permission
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.transaction import atomic
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from guardian.backends import object_grants_cache
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework.serializers import BaseSerializer

from authentik.blueprints.models import ManagedModel
from authentik.lib.models import SerializerModel, SimpleThroughModel

if TYPE_CHECKING:
    from authentik.core.models import User

GRANTS_ATTRIBUTE = "object_grants"


class Role(SerializerModel, ManagedModel):
    """RBAC role, which can have different permissions (both global and per-object) attached
    to it."""

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True, primary_key=True)
    name = models.TextField(unique=True)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.rbac.api.roles import RoleSerializer

        return RoleSerializer

    def __str__(self) -> str:
        return f"Role {self.name}"

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        permissions = [
            ("assign_role_permissions", _("Can assign permissions to roles")),
            ("unassign_role_permissions", _("Can unassign permissions from roles")),
        ]

    def assign_perms(
        self,
        perms: str | list[str] | Permission | list[Permission],
        obj: models.Model | None = None,
    ):
        """Assign permission to role, can handle multiple permissions,
        but when assigning multiple permissions to an object the permissions
        must all belong to the object given"""
        if not isinstance(perms, list):
            perms = [perms]
        with atomic():
            for perm in perms:
                assign_perm(perm, self, obj)

    def remove_perms(
        self,
        perms: str | list[str] | Permission | list[Permission],
        obj: models.Model | None = None,
    ):
        """Assign permission to role, can handle multiple permissions,
        but when assigning multiple permissions to an object the permissions
        must all belong to the object given"""
        if isinstance(perms, str):
            perms = [perms]
        with atomic():
            for perm in perms:
                remove_perm(perm, self, obj)


class InitialPermissions(SerializerModel):
    """Assigns permissions for newly created objects."""

    name = models.TextField(max_length=150, unique=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(
        Permission, blank=True, through="InitialPermissionsPermission"
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.rbac.api.initial_permissions import InitialPermissionsSerializer

        return InitialPermissionsSerializer

    def __str__(self) -> str:
        return f"Initial Permissions for Role #{self.role_id}."

    class Meta:
        verbose_name = _("Initial Permissions")
        verbose_name_plural = _("Initial Permissions")


class InitialPermissionsPermission(SimpleThroughModel):
    initial_permissions = models.ForeignKey(
        InitialPermissions, on_delete=models.CASCADE, db_column="initialpermissions_id"
    )
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = "authentik_rbac_initialpermissions_permissions"
        unique_together = (("initial_permissions", "permission"),)
        verbose_name = _("Initial Permissions Permission")
        verbose_name_plural = _("Initial Permissions Permissions")

    def __str__(self):
        return (
            f"InitialPermissionsPermission for InitialPermissions {self.initial_permissions_id} "
            f"and Permission {self.permission_id}."
        )


class SystemPermission(models.Model):
    """System-wide permissions that are not related to any direct
    database model"""

    class Meta:
        managed = False
        default_permissions = ()
        verbose_name = _("System permission")
        verbose_name_plural = _("System permissions")
        permissions = [
            ("view_system_info", _("Can view system info")),
            ("access_admin_interface", _("Can access admin interface")),
            ("view_system_settings", _("Can view system settings")),
            ("edit_system_settings", _("Can edit system settings")),
            ("view_media_files", _("Can view media files")),
            ("manage_media_files", _("Can manage media files")),
        ]

    def __str__(self) -> str:
        return "System Permission"


CUSTOM_PERMISSION_PREFIX = "custom_"


class CustomPermissionManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(codename__startswith=CUSTOM_PERMISSION_PREFIX)


class CustomPermission(SerializerModel, Permission):
    """The permissions admins define. This is a proxy model to make API and blueprints simple."""

    objects = CustomPermissionManager()

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.rbac.api.custom_permissions import CustomPermissionSerializer

        return CustomPermissionSerializer

    def __str__(self) -> str:
        return f"Custom permission {self.codename}"

    class Meta:
        proxy = True
        verbose_name = _("Custom permission")
        verbose_name_plural = _("Custom permissions")


class PermissionCheck(SerializerModel):
    """Python snippet with the final say on access to the API endpoints it is bound to"""

    check_uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.TextField(unique=True)
    expression = models.TextField()
    endpoints = ArrayField(models.TextField())

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.rbac.api.permission_checks import PermissionCheckSerializer

        return PermissionCheckSerializer

    def __str__(self) -> str:
        return f"Permission check {self.name}"

    @staticmethod
    def skipped_for(user: User) -> bool:
        """Superusers automatically pass every check"""
        return user.is_superuser

    def defines(self, function: str) -> bool:
        from authentik.rbac.evaluator import PermissionCheckEvaluator

        return function in PermissionCheckEvaluator.defined_functions(self.expression)

    def run(self, function: str, request: HttpRequest, endpoint: str | None, *args) -> Any:
        from authentik.rbac.evaluator import PermissionCheckEvaluator

        with object_grants_cache(request.__dict__.setdefault(GRANTS_ATTRIBUTE, {})):
            return PermissionCheckEvaluator(self, request, endpoint).run(function, *args)

    class Meta:
        verbose_name = _("Permission check")
        verbose_name_plural = _("Permission checks")
