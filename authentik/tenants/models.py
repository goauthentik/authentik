"""Tenant models"""

import re
from uuid import uuid4

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin, TenantMixin, post_schema_sync
from django_tenants.utils import get_tenant_base_schema
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.models import SerializerModel
from authentik.lib.utils.time import timedelta_string_validator

LOGGER = get_logger()


VALID_SCHEMA_NAME = re.compile(r"^t_[a-z0-9]{1,61}$")

DEFAULT_TOKEN_DURATION = "days=1"  # nosec
DEFAULT_TOKEN_LENGTH = 60
DEFAULT_REPUTATION_LOWER_LIMIT = -5
DEFAULT_REPUTATION_UPPER_LIMIT = 5


def _validate_schema_name(name):
    if not VALID_SCHEMA_NAME.match(name):
        raise ValidationError(
            _(
                "Schema name must start with t_, only contain lowercase letters and numbers and "
                "be less than 63 characters."
            )
        )


class Tenant(TenantMixin, SerializerModel):
    """Tenant"""

    tenant_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    schema_name = models.CharField(
        max_length=63, unique=True, db_index=True, validators=[_validate_schema_name]
    )
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
    event_retention = models.TextField(
        default="days=365",
        validators=[timedelta_string_validator],
        help_text=_(
            "Events will be deleted after this duration.(Format: weeks=3;days=2;hours=3,seconds=2)."
        ),
    )
    reputation_lower_limit = models.IntegerField(
        help_text=_("Reputation cannot decrease lower than this value. Zero or negative."),
        default=DEFAULT_REPUTATION_LOWER_LIMIT,
        validators=[MaxValueValidator(0)],
    )
    reputation_upper_limit = models.IntegerField(
        help_text=_("Reputation cannot increase higher than this value. Zero or positive."),
        default=DEFAULT_REPUTATION_UPPER_LIMIT,
        validators=[MinValueValidator(0)],
    )
    footer_links = models.JSONField(
        help_text=_("The option configures the footer links on the flow executor pages."),
        default=list,
        blank=True,
    )
    gdpr_compliance = models.BooleanField(
        help_text=_(
            "When enabled, all the events caused by a user "
            "will be deleted upon the user's deletion."
        ),
        default=True,
    )
    impersonation = models.BooleanField(
        help_text=_("Globally enable/disable impersonation."), default=True
    )
    impersonation_require_reason = models.BooleanField(
        help_text=_("Require administrators to provide a reason for impersonating a user."),
        default=True,
    )
    default_token_duration = models.TextField(
        help_text=_("Default token duration"),
        default=DEFAULT_TOKEN_DURATION,
        validators=[timedelta_string_validator],
    )
    default_token_length = models.PositiveIntegerField(
        help_text=_("Default token length"),
        default=DEFAULT_TOKEN_LENGTH,
        validators=[MinValueValidator(1)],
    )

    def save(self, *args, **kwargs):
        if self.schema_name == get_tenant_base_schema() and not settings.TEST:
            raise IntegrityError(f"Cannot create schema named {self.schema_name}")
        super().save(*args, **kwargs)

    @property
    def serializer(self) -> Serializer:
        from authentik.tenants.api.tenants import TenantSerializer

        return TenantSerializer

    def __str__(self) -> str:
        return f"Tenant {self.name}"

    class Meta:
        verbose_name = _("Tenant")
        verbose_name_plural = _("Tenants")


class Domain(DomainMixin, SerializerModel):
    """Tenant domain"""

    tenant = models.ForeignKey(
        Tenant, db_index=True, related_name="domains", on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f"Domain {self.domain}"

    @property
    def serializer(self) -> Serializer:
        from authentik.tenants.api.domains import DomainSerializer

        return DomainSerializer

    class Meta:
        verbose_name = _("Domain")
        verbose_name_plural = _("Domains")


@receiver(post_schema_sync, sender=TenantMixin)
def tenant_needs_sync(sender, tenant, **kwargs):
    """Reconcile apps for a specific tenant on creation"""
    if tenant.ready:
        return

    with tenant:
        for app in apps.get_app_configs():
            if isinstance(app, ManagedAppConfig):
                app._reconcile(ManagedAppConfig.RECONCILE_TENANT_CATEGORY)

    tenant.ready = True
    tenant.save()
