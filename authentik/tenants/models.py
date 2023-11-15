"""Tenant models"""
from uuid import uuid4

from django.apps import apps
from django.core.management import call_command
from django.db import connections, models
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin, TenantMixin, post_schema_sync
from django_tenants.postgresql_backend.base import _check_schema_name
from django_tenants.utils import (
    get_creation_fakes_migrations,
    get_tenant_base_schema,
    get_tenant_database_alias,
    schema_exists,
)
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.models import SerializerModel
from authentik.tenants.clone import CloneSchema

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
            "When enabled, all the events caused by a user "
            "will be deleted upon the user's deletion."
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

    def create_schema(self, check_if_exists=False, sync_schema=True, verbosity=1):
        """
        Creates the schema 'schema_name' for this tenant. Optionally checks if
        the schema already exists before creating it. Returns true if the
        schema was created, false otherwise.
        """

        # safety check
        connection = connections[get_tenant_database_alias()]
        _check_schema_name(self.schema_name)
        cursor = connection.cursor()

        if check_if_exists and schema_exists(self.schema_name):
            return False

        fake_migrations = get_creation_fakes_migrations()

        if sync_schema:
            if fake_migrations:
                # copy tables and data from provided model schema
                base_schema = get_tenant_base_schema()
                clone_schema = CloneSchema()
                clone_schema.clone_schema(base_schema, self.schema_name)

                call_command(
                    "migrate_schemas",
                    tenant=True,
                    fake=True,
                    schema_name=self.schema_name,
                    interactive=False,
                    verbosity=verbosity,
                )
            else:
                # create the schema
                cursor.execute('CREATE SCHEMA "%s"' % self.schema_name)
                call_command(
                    "migrate_schemas",
                    tenant=True,
                    schema_name=self.schema_name,
                    interactive=False,
                    verbosity=verbosity,
                )

        connection.set_schema_to_public()

    def save(self, *args, **kwargs):
        if self.schema_name == "template":
            raise Exception("Cannot create schema named template")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.schema_name in ("public", "template"):
            raise Exception("Cannot delete schema public or template")
        super().delete(*args, **kwargs)

    @property
    def serializer(self) -> Serializer:
        from authentik.tenants.api import TenantSerializer

        return TenantSerializer

    def __str__(self) -> str:
        return f"Tenant {self.name}"

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
def tenant_needs_sync(sender, tenant, **kwargs):
    if tenant.ready:
        return

    with tenant:
        for app in apps.get_app_configs():
            if isinstance(app, ManagedAppConfig):
                app._reconcile(ManagedAppConfig.RECONCILE_TENANT_PREFIX)

    tenant.ready = True
    tenant.save()
