"""write stage models"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.models import Group
from authentik.flows.models import Stage


class UserCreationMode(models.TextChoices):
    """Behavior of user_write stage when a user is not set in the flow context"""

    NEVER_CREATE = "never_create"
    CREATE_WHEN_REQUIRED = "create_when_required"
    ALWAYS_CREATE = "always_create"


class UserWriteStage(Stage):
    """Writes currently pending data into the pending user, or if no user exists,
    creates a new user with the data."""

    user_creation_mode = models.TextField(
        choices=UserCreationMode.choices,
        default=UserCreationMode.CREATE_WHEN_REQUIRED,
    )

    create_users_as_inactive = models.BooleanField(
        default=False,
        help_text=_("When set, newly created users are inactive and cannot login."),
    )

    create_users_group = models.ForeignKey(
        Group,
        null=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        help_text=_("Optionally add newly created users to this group."),
    )

    user_path_template = models.TextField(
        default="",
        blank=True,
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.user_write.api import UserWriteStageSerializer

        return UserWriteStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.user_write.stage import UserWriteStageView

        return UserWriteStageView

    @property
    def component(self) -> str:
        return "ak-stage-user-write-form"

    class Meta:
        verbose_name = _("User Write Stage")
        verbose_name_plural = _("User Write Stages")
