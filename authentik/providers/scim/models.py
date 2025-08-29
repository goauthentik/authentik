"""SCIM Provider models"""

from typing import Any, Self
from uuid import uuid4

from django.db import models
from django.db.models import QuerySet
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import Actor
from rest_framework.serializers import Serializer

from authentik.core.models import BackchannelProvider, Group, PropertyMapping, User, UserTypes
from authentik.lib.models import SerializerModel
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider


class SCIMProviderUser(SerializerModel):
    """Mapping of a user and provider to a SCIM user ID"""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    scim_id = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey("SCIMProvider", on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.scim.api.users import SCIMProviderUserSerializer

        return SCIMProviderUserSerializer

    class Meta:
        unique_together = (("scim_id", "user", "provider"),)

    def __str__(self) -> str:
        return f"SCIM Provider User {self.user_id} to {self.provider_id}"


class SCIMProviderGroup(SerializerModel):
    """Mapping of a group and provider to a SCIM user ID"""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    scim_id = models.TextField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    provider = models.ForeignKey("SCIMProvider", on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.scim.api.groups import SCIMProviderGroupSerializer

        return SCIMProviderGroupSerializer

    class Meta:
        unique_together = (("scim_id", "group", "provider"),)

    def __str__(self) -> str:
        return f"SCIM Provider Group {self.group_id} to {self.provider_id}"


class SCIMCompatibilityMode(models.TextChoices):
    """SCIM compatibility mode"""

    DEFAULT = "default", _("Default")
    AWS = "aws", _("AWS")
    SLACK = "slack", _("Slack")


class SCIMProvider(OutgoingSyncProvider, BackchannelProvider):
    """SCIM 2.0 provider to create users and groups in external applications"""

    exclude_users_service_account = models.BooleanField(default=False)

    filter_group = models.ForeignKey(
        "authentik_core.group", on_delete=models.SET_DEFAULT, default=None, null=True
    )

    url = models.TextField(help_text=_("Base URL to SCIM requests, usually ends in /v2"))
    token = models.TextField(help_text=_("Authentication token"))
    verify_certificates = models.BooleanField(default=True)

    property_mappings_group = models.ManyToManyField(
        PropertyMapping,
        default=None,
        blank=True,
        help_text=_("Property mappings used for group creation/updating."),
    )

    compatibility_mode = models.CharField(
        max_length=30,
        choices=SCIMCompatibilityMode.choices,
        default=SCIMCompatibilityMode.DEFAULT,
        verbose_name=_("SCIM Compatibility Mode"),
        help_text=_("Alter authentik behavior for vendor-specific SCIM implementations."),
    )

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/scim.png")

    @property
    def sync_actor(self) -> Actor:
        from authentik.providers.scim.tasks import scim_sync

        return scim_sync

    def client_for_model(
        self, model: type[User | Group | SCIMProviderUser | SCIMProviderGroup]
    ) -> BaseOutgoingSyncClient[User | Group, Any, Any, Self]:
        if issubclass(model, User | SCIMProviderUser):
            from authentik.providers.scim.clients.users import SCIMUserClient

            return SCIMUserClient(self)
        if issubclass(model, Group | SCIMProviderGroup):
            from authentik.providers.scim.clients.groups import SCIMGroupClient

            return SCIMGroupClient(self)
        raise ValueError(f"Invalid model {model}")

    def get_object_qs(self, type: type[User | Group]) -> QuerySet[User | Group]:
        if type == User:
            # Get queryset of all users with consistent ordering
            # according to the provider's settings
            base = User.objects.prefetch_related("scimprovideruser_set").all().exclude_anonymous()
            if self.exclude_users_service_account:
                base = base.exclude(type=UserTypes.SERVICE_ACCOUNT).exclude(
                    type=UserTypes.INTERNAL_SERVICE_ACCOUNT
                )
            if self.filter_group:
                base = base.filter(ak_groups__in=[self.filter_group])
            return base.order_by("pk")
        if type == Group:
            # Get queryset of all groups with consistent ordering
            return Group.objects.prefetch_related("scimprovidergroup_set").all().order_by("pk")
        raise ValueError(f"Invalid type {type}")

    @property
    def component(self) -> str:
        return "ak-provider-scim-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.scim.api.providers import SCIMProviderSerializer

        return SCIMProviderSerializer

    def __str__(self):
        return f"SCIM Provider {self.name}"

    class Meta:
        verbose_name = _("SCIM Provider")
        verbose_name_plural = _("SCIM Providers")


class SCIMMapping(PropertyMapping):
    """Map authentik data to outgoing SCIM requests"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-provider-scim-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.scim.api.property_mappings import SCIMMappingSerializer

        return SCIMMappingSerializer

    def __str__(self):
        return f"SCIM Provider Mapping {self.name}"

    class Meta:
        verbose_name = _("SCIM Provider Mapping")
        verbose_name_plural = _("SCIM Provider Mappings")
