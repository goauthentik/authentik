"""Google workspace sync provider"""

from typing import Any, Self
from uuid import uuid4

from django.db import models
from django.db.models import QuerySet
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import Actor
from google.oauth2.service_account import Credentials
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


def default_scopes() -> list[str]:
    return [
        "https://www.googleapis.com/auth/admin.directory.user",
        "https://www.googleapis.com/auth/admin.directory.group",
        "https://www.googleapis.com/auth/admin.directory.group.member",
        "https://www.googleapis.com/auth/admin.directory.domain.readonly",
    ]


class GoogleWorkspaceProviderUser(SerializerModel):
    """Mapping of a user and provider to a Google user ID"""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    google_id = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey("GoogleWorkspaceProvider", on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.google_workspace.api.users import (
            GoogleWorkspaceProviderUserSerializer,
        )

        return GoogleWorkspaceProviderUserSerializer

    class Meta:
        verbose_name = _("Google Workspace Provider User")
        verbose_name_plural = _("Google Workspace Provider Users")
        unique_together = (("google_id", "user", "provider"),)

    def __str__(self) -> str:
        return f"Google Workspace Provider User {self.user_id} to {self.provider_id}"


class GoogleWorkspaceProviderGroup(SerializerModel):
    """Mapping of a group and provider to a Google group ID"""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    google_id = models.TextField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    provider = models.ForeignKey("GoogleWorkspaceProvider", on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.google_workspace.api.groups import (
            GoogleWorkspaceProviderGroupSerializer,
        )

        return GoogleWorkspaceProviderGroupSerializer

    class Meta:
        verbose_name = _("Google Workspace Provider Group")
        verbose_name_plural = _("Google Workspace Provider Groups")
        unique_together = (("google_id", "group", "provider"),)

    def __str__(self) -> str:
        return f"Google Workspace Provider Group {self.group_id} to {self.provider_id}"


class GoogleWorkspaceProvider(OutgoingSyncProvider, BackchannelProvider):
    """Sync users from authentik into Google Workspace."""

    delegated_subject = models.EmailField()
    credentials = models.JSONField()
    scopes = models.TextField(default=",".join(default_scopes()))

    default_group_email_domain = models.TextField()
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
        from authentik.enterprise.providers.google_workspace.tasks import google_workspace_sync

        return google_workspace_sync

    def client_for_model(
        self,
        model: type[User | Group | GoogleWorkspaceProviderUser | GoogleWorkspaceProviderGroup],
    ) -> BaseOutgoingSyncClient[User | Group, Any, Any, Self]:
        if issubclass(model, User | GoogleWorkspaceProviderUser):
            from authentik.enterprise.providers.google_workspace.clients.users import (
                GoogleWorkspaceUserClient,
            )

            return GoogleWorkspaceUserClient(self)
        if issubclass(model, Group | GoogleWorkspaceProviderGroup):
            from authentik.enterprise.providers.google_workspace.clients.groups import (
                GoogleWorkspaceGroupClient,
            )

            return GoogleWorkspaceGroupClient(self)
        raise ValueError(f"Invalid model {model}")

    def get_object_qs(self, type: type[User | Group]) -> QuerySet[User | Group]:
        if type == User:
            # Get queryset of all users with consistent ordering
            # according to the provider's settings
            base = (
                User.objects.prefetch_related("googleworkspaceprovideruser_set")
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
                Group.objects.prefetch_related("googleworkspaceprovidergroup_set")
                .all()
                .order_by("pk")
            )
        raise ValueError(f"Invalid type {type}")

    def google_credentials(self):
        return {
            "credentials": Credentials.from_service_account_info(
                self.credentials, scopes=self.scopes.split(",")
            ).with_subject(self.delegated_subject),
        }

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/google.svg")

    @property
    def component(self) -> str:
        return "ak-provider-google-workspace-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.google_workspace.api.providers import (
            GoogleWorkspaceProviderSerializer,
        )

        return GoogleWorkspaceProviderSerializer

    def __str__(self):
        return f"Google Workspace Provider {self.name}"

    class Meta:
        verbose_name = _("Google Workspace Provider")
        verbose_name_plural = _("Google Workspace Providers")


class GoogleWorkspaceProviderMapping(PropertyMapping):
    """Map authentik data to outgoing Google requests"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-provider-google-workspace-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.google_workspace.api.property_mappings import (
            GoogleWorkspaceProviderMappingSerializer,
        )

        return GoogleWorkspaceProviderMappingSerializer

    def __str__(self):
        return f"Google Workspace Provider Mapping {self.name}"

    class Meta:
        verbose_name = _("Google Workspace Provider Mapping")
        verbose_name_plural = _("Google Workspace Provider Mappings")
