"""authentik admin models"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import IntegrityError, models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.lib.models import InternallyManagedMixin, SerializerModel
from authentik.lib.utils.time import timedelta_string_validator

DEFAULT_TOKEN_DURATION = "days=1"  # nosec
DEFAULT_TOKEN_LENGTH = 60
DEFAULT_REPUTATION_LOWER_LIMIT = -5
DEFAULT_REPUTATION_UPPER_LIMIT = 5


class SystemSettings(InternallyManagedMixin, SerializerModel):
    id = models.BooleanField(primary_key=True, default=True)

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

    pagination_default_page_size = models.PositiveIntegerField(
        help_text=_("Default page size for API responses, if no size was requested."),
        default=20,
    )
    pagination_max_page_size = models.PositiveIntegerField(
        help_text=_("Maximum page size"),
        default=100,
    )

    flags = models.JSONField(default=dict)

    class Meta:
        verbose_name = _("System settings")
        verbose_name_plural = _("System settings")
        default_permissions = []

    def __str__(self):
        return "System settings"

    def save(self, *args, **kwargs):
        if not self.pk:
            raise IntegrityError("Only one instance of system settings is allowed")
        super().save(*args, **kwargs)

    @property
    def serializer(self) -> Serializer:
        from authentik.admin.api.settings import SettingsSerializer

        return SettingsSerializer


class VersionHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField()
    version = models.TextField()
    build = models.TextField()

    class Meta:
        managed = False
        db_table = "authentik_version_history"
        ordering = ("-timestamp",)
        verbose_name = _("Version history")
        verbose_name_plural = _("Version history")
        default_permissions = []

    def __str__(self):
        return f"{self.version}.{self.build} ({self.timestamp})"
