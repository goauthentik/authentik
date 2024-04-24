from typing import Any, Self

from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from google.oauth2.service_account import Credentials
from rest_framework.serializers import Serializer

from authentik.core.models import (
    BackchannelProvider,
    Group,
    PropertyMapping,
    User,
    UserTypes,
)
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider


class GoogleProvider(OutgoingSyncProvider, BackchannelProvider):
    """Sync users from authentik into Google Workspace."""

    delegated_subject = models.EmailField()
    credentials = models.JSONField()
    scopes = models.TextField(default="https://www.googleapis.com/auth/admin.directory.user")

    exclude_users_service_account = models.BooleanField(default=False)

    filter_group = models.ForeignKey(
        "authentik_core.group", on_delete=models.SET_DEFAULT, default=None, null=True
    )

    property_mappings_group = models.ManyToManyField(
        PropertyMapping,
        default=None,
        blank=True,
        help_text=_("Property mappings used for group creation/updating."),
    )

    def client_for_model(
        self, model: type[User | Group]
    ) -> BaseOutgoingSyncClient[User | Group, Any, Self]:
        if issubclass(model, User):
            from authentik.enterprise.providers.google.clients.users import GoogleUserClient

            return GoogleUserClient(self)
        raise ValueError(f"Invalid model {model}")

    def get_object_qs(self, type: type[User | Group]) -> QuerySet[User | Group]:
        if type == User:
            # Get queryset of all users with consistent ordering
            # according to the provider's settings
            base = User.objects.all().exclude_anonymous()
            if self.exclude_users_service_account:
                base = base.exclude(type=UserTypes.SERVICE_ACCOUNT).exclude(
                    type=UserTypes.INTERNAL_SERVICE_ACCOUNT
                )
            if self.filter_group:
                base = base.filter(ak_groups__in=[self.filter_group])
            return base.order_by("pk")
        if type == Group:
            # Get queryset of all groups with consistent ordering
            return Group.objects.all().order_by("pk")
        raise ValueError(f"Invalid type {type}")

    def google_credentials(self):
        return Credentials.from_service_account_info(
            self.credentials, scopes=self.scopes.split(",")
        ).with_subject(self.delegated_subject)

    @property
    def component(self) -> str:
        return "ak-provider-google-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.google.api.providers import GoogleProviderSerializer

        return GoogleProviderSerializer


class GoogleProviderMapping(PropertyMapping):
    """Map authentik data to outgoing Google requests"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-google-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.google.api.property_mappings import (
            GoogleProviderMappingSerializer,
        )

        return GoogleProviderMappingSerializer

    def __str__(self):
        return f"Google Provider Mapping {self.name}"

    class Meta:
        verbose_name = _("Google Provider Mapping")
        verbose_name_plural = _("Google Provider Mappings")


class GoogleProviderUser(models.Model):
    """Mapping of a user and provider to a Google user ID"""

    id = models.TextField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(GoogleProvider, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("id", "user", "provider"),)

    def __str__(self) -> str:
        return f"Google User {self.user.username} to {self.provider.name}"


class GoogleProviderGroup(models.Model):
    """Mapping of a group and provider to a Google user ID"""

    id = models.TextField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    provider = models.ForeignKey(GoogleProvider, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("id", "group", "provider"),)

    def __str__(self) -> str:
        return f"Google Group {self.group.name} to {self.provider.name}"
