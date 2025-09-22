"""Microsoft Entra sync provider"""

from typing import Any, Self
from uuid import uuid4

from azure.identity.aio import ClientSecretCredential
from django.db import models
from django.db.models import QuerySet
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import Actor
from rest_framework.serializers import Serializer

from authentik.core.models import (
    BackchannelProvider,
    Group,
    PropertyMapping,
    User,
    UserTypes,
)
from authentik.lib.models import SerializerModel
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient
from authentik.lib.sync.outgoing.models import OutgoingSyncDeleteAction, OutgoingSyncProvider


class MicrosoftEntraProviderUser(SerializerModel):
    """Mapping of a user and provider to a Microsoft user ID"""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    microsoft_id = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey("MicrosoftEntraProvider", on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.microsoft_entra.api.users import (
            MicrosoftEntraProviderUserSerializer,
        )

        return MicrosoftEntraProviderUserSerializer

    class Meta:
        verbose_name = _("Microsoft Entra Provider User")
        verbose_name_plural = _("Microsoft Entra Provider User")
        unique_together = (("microsoft_id", "user", "provider"),)

    def __str__(self) -> str:
        return f"Microsoft Entra Provider User {self.user_id} to {self.provider_id}"


class MicrosoftEntraProviderGroup(SerializerModel):
    """Mapping of a group and provider to a Microsoft group ID"""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    microsoft_id = models.TextField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    provider = models.ForeignKey("MicrosoftEntraProvider", on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.microsoft_entra.api.groups import (
            MicrosoftEntraProviderGroupSerializer,
        )

        return MicrosoftEntraProviderGroupSerializer

    class Meta:
        verbose_name = _("Microsoft Entra Provider Group")
        verbose_name_plural = _("Microsoft Entra Provider Groups")
        unique_together = (("microsoft_id", "group", "provider"),)

    def __str__(self) -> str:
        return f"Microsoft Entra Provider Group {self.group_id} to {self.provider_id}"


class MicrosoftEntraProvider(OutgoingSyncProvider, BackchannelProvider):
    """Sync users from authentik into Microsoft Entra."""

    client_id = models.TextField()
    client_secret = models.TextField()
    tenant_id = models.TextField()

    exclude_users_service_account = models.BooleanField(default=False)
    user_delete_action = models.TextField(
        choices=OutgoingSyncDeleteAction.choices, default=OutgoingSyncDeleteAction.DELETE
    )
    group_delete_action = models.TextField(
        choices=OutgoingSyncDeleteAction.choices, default=OutgoingSyncDeleteAction.DELETE
    )
    filter_group = models.ForeignKey(
        "authentik_core.group", on_delete=models.SET_DEFAULT, default=None, null=True
    )

    property_mappings_group = models.ManyToManyField(
        PropertyMapping,
        default=None,
        blank=True,
        help_text=_("Property mappings used for group creation/updating."),
    )

    @property
    def sync_actor(self) -> Actor:
        from authentik.enterprise.providers.microsoft_entra.tasks import microsoft_entra_sync

        return microsoft_entra_sync

    def client_for_model(
        self,
        model: type[User | Group | MicrosoftEntraProviderUser | MicrosoftEntraProviderGroup],
    ) -> BaseOutgoingSyncClient[User | Group, Any, Any, Self]:
        if issubclass(model, User | MicrosoftEntraProviderUser):
            from authentik.enterprise.providers.microsoft_entra.clients.users import (
                MicrosoftEntraUserClient,
            )

            return MicrosoftEntraUserClient(self)
        if issubclass(model, Group | MicrosoftEntraProviderGroup):
            from authentik.enterprise.providers.microsoft_entra.clients.groups import (
                MicrosoftEntraGroupClient,
            )

            return MicrosoftEntraGroupClient(self)
        raise ValueError(f"Invalid model {model}")

    def get_object_qs(self, type: type[User | Group]) -> QuerySet[User | Group]:
        if type == User:
            # Get queryset of all users with consistent ordering
            # according to the provider's settings
            base = (
                User.objects.prefetch_related("microsoftentraprovideruser_set")
                .all()
                .exclude_anonymous()
            )
            if self.exclude_users_service_account:
                base = base.exclude(type=UserTypes.SERVICE_ACCOUNT).exclude(
                    type=UserTypes.INTERNAL_SERVICE_ACCOUNT
                )
            if self.filter_group:
                base = base.filter(ak_groups__in=[self.filter_group])
            return base.order_by("pk")
        if type == Group:
            # Get queryset of all groups with consistent ordering
            return (
                Group.objects.prefetch_related("microsoftentraprovidergroup_set")
                .all()
                .order_by("pk")
            )
        raise ValueError(f"Invalid type {type}")

    def microsoft_credentials(self):
        return {
            "credentials": ClientSecretCredential(
                self.tenant_id, self.client_id, self.client_secret
            )
        }

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/azuread.svg")

    @property
    def component(self) -> str:
        return "ak-provider-microsoft-entra-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.microsoft_entra.api.providers import (
            MicrosoftEntraProviderSerializer,
        )

        return MicrosoftEntraProviderSerializer

    def __str__(self):
        return f"Microsoft Entra Provider {self.name}"

    class Meta:
        verbose_name = _("Microsoft Entra Provider")
        verbose_name_plural = _("Microsoft Entra Providers")


class MicrosoftEntraProviderMapping(PropertyMapping):
    """Map authentik data to outgoing Microsoft requests"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-provider-microsoft-entra-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.microsoft_entra.api.property_mappings import (
            MicrosoftEntraProviderMappingSerializer,
        )

        return MicrosoftEntraProviderMappingSerializer

    def __str__(self):
        return f"Microsoft Entra Provider Mapping {self.name}"

    class Meta:
        verbose_name = _("Microsoft Entra Provider Mapping")
        verbose_name_plural = _("Microsoft Entra Provider Mappings")
