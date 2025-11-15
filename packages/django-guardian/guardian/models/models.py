from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from guardian.conf import settings as guardian_settings
from guardian.ctypes import get_content_type
from guardian.managers import (
    GroupObjectPermissionManager,
    RoleObjectPermissionManager,
    UserObjectPermissionManager,
)


class BaseObjectPermission(models.Model):
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return "{} | {} | {}".format(
            str(self.content_object),
            str(
                getattr(self, "user", False)
                or str(getattr(self, "group", False))
                or str(getattr(self, "role", False))
            ),
            str(self.permission.codename),
        )

    def save(self, *args, **kwargs) -> None:
        content_type = get_content_type(self.content_object)
        if content_type != self.permission.content_type:
            raise ValidationError(
                "Cannot persist permission not designed for this class (permission's type is "
                f"{self.permission.content_type} and object's type is {content_type})"
            )
        return super().save(*args, **kwargs)


class BaseGenericObjectPermission(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_pk = models.CharField(_("object ID"), max_length=255)
    content_object = GenericForeignKey(fk_field="object_pk")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["content_type", "object_pk"]),
        ]


# The Role* classes follow the User* and Group* class structures for now.
# TODO: restructure Role* classes.


class RoleObjectPermissionBase(BaseObjectPermission):
    role = models.ForeignKey(guardian_settings.role_model_label, on_delete=models.CASCADE)

    objects = RoleObjectPermissionManager()

    class Meta:
        abstract = True
        unique_together = ["role", "permission", "content_object"]


class RoleObjectPermissionAbstract(RoleObjectPermissionBase, BaseGenericObjectPermission):
    class Meta(RoleObjectPermissionBase.Meta, BaseGenericObjectPermission.Meta):
        abstract = True
        unique_together = ["role", "permission", "object_pk"]


class RoleObjectPermission(RoleObjectPermissionAbstract):
    class Meta(RoleObjectPermissionAbstract.Meta):
        abstract = False
        indexes = [
            models.Index(fields=["permission", "role", "content_type", "object_pk"]),
            models.Index(fields=["role", "content_type", "object_pk"]),
        ]


class RoleModelPermission(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    role = models.ForeignKey(guardian_settings.role_model_label, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["role", "permission"]
        indexes = [
            models.Index(fields=["permission", "role", "content_type"]),
            models.Index(fields=["role", "content_type"]),
        ]

    def __str__(self) -> str:
        return f"RoleModelPermission with role {self.role_id} and permission {self.permission_id}"


# The following classes are deprecated and will be removed in a future release.
# TODO: remove deprecated classes.


class UserObjectPermissionBase(BaseObjectPermission):
    user = models.ForeignKey(guardian_settings.user_model_label, on_delete=models.CASCADE)

    objects = UserObjectPermissionManager()

    class Meta:
        abstract = True
        unique_together = ["user", "permission", "content_object"]


class UserObjectPermissionAbstract(UserObjectPermissionBase, BaseGenericObjectPermission):
    class Meta(UserObjectPermissionBase.Meta, BaseGenericObjectPermission.Meta):
        abstract = True
        unique_together = ["user", "permission", "object_pk"]


class UserObjectPermission(UserObjectPermissionAbstract):
    class Meta(UserObjectPermissionAbstract.Meta):
        abstract = False
        indexes = [
            models.Index(fields=["permission", "user", "content_type", "object_pk"]),
            models.Index(fields=["user", "content_type", "object_pk"]),
        ]


class GroupObjectPermissionBase(BaseObjectPermission):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    objects = GroupObjectPermissionManager()

    class Meta:
        abstract = True
        unique_together = ["group", "permission", "content_object"]


class GroupObjectPermissionAbstract(GroupObjectPermissionBase, BaseGenericObjectPermission):
    class Meta(GroupObjectPermissionBase.Meta, BaseGenericObjectPermission.Meta):
        abstract = True
        unique_together = ["group", "permission", "object_pk"]


class GroupObjectPermission(GroupObjectPermissionAbstract):
    class Meta(GroupObjectPermissionAbstract.Meta):
        abstract = False
        indexes = [
            models.Index(fields=["permission", "group", "content_type", "object_pk"]),
            models.Index(fields=["group", "content_type", "object_pk"]),
        ]
