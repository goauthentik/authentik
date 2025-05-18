"""RBAC models"""

from uuid import uuid4

from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission
from django.db import models
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm
from rest_framework.serializers import BaseSerializer

from authentik.lib.models import SerializerModel
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


class Role(SerializerModel):
    """RBAC role, which can have different permissions (both global and per-object) attached
    to it."""

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True, primary_key=True)
    # Due to the way django and django-guardian work, this is somewhat of a hack.
    # Django and django-guardian allow for setting permissions on users and groups, but they
    # only allow for a custom user object, not a custom group object, which is why
    # we have both authentik and django groups. With this model, we use the inbuilt group system
    # for RBAC. This means that every Role needs a single django group that its assigned to
    # which will hold all of the actual permissions
    # The main advantage of that is that all the permission checking just works out of the box,
    # as these permissions are checked by default by django and most other libraries that build
    # on top of django
    group = models.OneToOneField("auth.Group", on_delete=models.CASCADE)

    # name field has the same constraints as the group model
    name = models.TextField(max_length=150, unique=True)

    def assign_permission(self, *perms: str, obj: models.Model | None = None):
        """Assign permission to role, can handle multiple permissions,
        but when assigning multiple permissions to an object the permissions
        must all belong to the object given"""
        with atomic():
            for perm in perms:
                assign_perm(perm, self.group, obj)

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
            ("assign_role_permissions", _("Can assign permissions to users")),
            ("unassign_role_permissions", _("Can unassign permissions from users")),
        ]


class InitialPermissionsMode(models.TextChoices):
    """Determines which entity the initial permissions are assigned to."""

    USER = "user", _("User")
    ROLE = "role", _("Role")


class InitialPermissions(SerializerModel):
    """Assigns permissions for newly created objects."""

    name = models.TextField(max_length=150, unique=True)
    mode = models.CharField(choices=InitialPermissionsMode.choices)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(Permission, blank=True)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.rbac.api.initial_permissions import InitialPermissionsSerializer

        return InitialPermissionsSerializer

    def __str__(self) -> str:
        return f"Initial Permissions for Role #{self.role_id}, applying to #{self.mode}"

    class Meta:
        verbose_name = _("Initial Permissions")
        verbose_name_plural = _("Initial Permissions")


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
        ]

    def __str__(self) -> str:
        return "System Permission"
