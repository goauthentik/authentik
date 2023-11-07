"""Tenant models"""
from uuid import UUID, uuid4

from django.db import models
from django.db.models.deletion import ProtectedError
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.lib.generators import generate_key
from authentik.lib.models import SerializerModel

LOGGER = get_logger()


class Tenant(SerializerModel):
    """Tenant"""

    tenant_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    domain_regex = models.TextField(help_text=_("Domain regex that activates this tenant."))

    avatars = models.TextField(
        help_text=_("Configure how authentik should show avatars for users."),
        default="gravatar,initials",
    )
    default_user_change_name = models.BooleanField(
        help_text=_("Enable the ability for users to change their name."), default=True
    )
    default_user_change_email = models.BooleanField(
        help_text=_("Enable the ability for users to change their email address."), default=False
    )
    default_user_change_username = models.BooleanField(
        help_text=_("Enable the ability for users to change their username."), default=False
    )
    gdpr_compliance = models.BooleanField(
        help_text=_(
            "When enabled, all the events caused by a user will be deleted upon the user's deletion."
        ),
        default=True,
    )
    impersonation = models.BooleanField(
        help_text=_("Globally enable/disable impersonation."), default=True
    )
    footer_links = models.JSONField(
        help_text=_("The option configures the footer links on the flow executor pages."),
        default=list,
        blank=True,
    )

    @property
    def serializer(self) -> Serializer:
        from authentik.tenants.api import SettingsSerializer

        return SettingsSerializer

    def __str__(self) -> str:
        return f"Tenant {self.domain_regex}"

    class Meta:
        verbose_name = _("Tenant")
        verbose_name_plural = _("Tenants")


@receiver(pre_delete, sender=Tenant)
def prevent_default_tenant_deletion(sender, instance, using, **kwargs):
    if instance.domain_regex == "*":
        raise ProtectedError(_("Default tenant cannot be deleted"))


def get_default_tenant() -> Tenant:
    return Tenant.objects.get(domain_regex=".*")


def get_default_tenant_uuid() -> UUID:
    return get_default_tenant().tenant_uuid


class TenantModel(models.Model):
    """Base tenant model for models that are tenant-specific"""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, default=get_default_tenant_uuid)

    class Meta:
        abstract = True
