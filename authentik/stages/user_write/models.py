"""write stage models"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.models import Group
from authentik.flows.models import Stage


class UserWriteStage(Stage):
    """Writes currently pending data into the pending user, or if no user exists,
    creates a new user with the data."""

    can_create_users = models.BooleanField(
        default=True,
        help_text=_(
            (
                "When set, this stage can create users. "
                "If not enabled and no user is available, stage will fail."
            )
        ),
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
