"""RBAC models"""

from uuid import uuid4

from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission
from django.db import models
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework.serializers import BaseSerializer

from authentik.blueprints.models import ManagedModel
from authentik.lib.models import SerializerModel, SimpleThroughModel
from authentik.lib.utils.reflection import get_apps


def get_permission_choices():
    all_perms = []
    for app in get_apps():
        for model in app.get_models():
            for perm, _desc in _get_all_permissions(model._meta):
                all_perms.append((model, perm))
    return sorted(
        [
            (
                f"{model._meta.app_label}.{perm}",
                f"{model._meta.app_label}.{perm}",
            )
            for model, perm in all_perms
        ]
    )


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
