"""Tenant models"""
from uuid import uuid4

from django.db import models
from django.db.models.deletion import ProtectedError
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin, TenantMixin, post_schema_sync
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.lib.models import SerializerModel

LOGGER = get_logger()


class Tenant(TenantMixin, SerializerModel):
    """Tenant"""

    tenant_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField()

    auto_create_schema = True
    auto_drop_schema = True
    ready = models.BooleanField(default=False)

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
    reputation_expiry = models.PositiveBigIntegerField(
        help_text=_("Configure how long reputation scores should be saved for in seconds."),
        default=86400,
    )

    @property
    def serializer(self) -> Serializer:
        from authentik.tenants.api import TenantSerializer

        return TenantSerializer

    def __str__(self) -> str:
        return f"Tenant {self.domain_regex}"

    class Meta:
        verbose_name = _("Tenant")
        verbose_name_plural = _("Tenants")


class Domain(DomainMixin, SerializerModel):
    def __str__(self) -> str:
        return f"Domain {self.domain}"

    @property
    def serializer(self) -> Serializer:
        from authentik.tenants.api import DomainSerializer

        return DomainSerializer

    class Meta:
        verbose_name = _("Domain")
        verbose_name_plural = _("Domains")


@receiver(post_schema_sync, sender=TenantMixin)
def tenant_ready(sender, tenant, **kwargs):
    tenant.ready = True
    tenant.save()
