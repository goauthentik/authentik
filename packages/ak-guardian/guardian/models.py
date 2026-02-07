from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from guardian.conf import settings as guardian_settings
from guardian.utils import get_content_type


class RoleObjectPermission(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    role = models.ForeignKey(guardian_settings.role_model_label, on_delete=models.CASCADE)
    object_pk = models.CharField(_("object ID"), max_length=255)
    content_object = GenericForeignKey(fk_field="object_pk")

    class Meta:
        unique_together = ["role", "permission", "object_pk"]
        indexes = [
            models.Index(fields=["permission", "role", "content_type", "object_pk"]),
            models.Index(fields=["role", "content_type", "object_pk"]),
        ]

    def __str__(self) -> str:
        return f"{str(self.content_object)} | {str(self.role)} | {str(self.permission.codename)}"

    def save(self, *args, **kwargs) -> None:
        content_type = get_content_type(self.content_object)
        if content_type != self.permission.content_type:
            raise ValidationError(
                "Cannot persist permission not designed for this class (permission's type is "
                f"{self.permission.content_type} and object's type is {content_type})"
            )
        return super().save(*args, **kwargs)


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
