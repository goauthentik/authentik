"""Enterprise password stage models."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik.core.models import User


class UserPasswordLoginState(models.Model):
    """Persistent password-login failures and lock state for a user."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="password_login_state",
    )
    failed_attempts = models.PositiveIntegerField(default=0, editable=False)
    locked_at = models.DateTimeField(null=True, editable=False)

    class Meta:
        verbose_name = _("User password login state")
        verbose_name_plural = _("User password login states")
        default_permissions = []
        constraints = [
            models.CheckConstraint(
                condition=models.Q(locked_at__isnull=True) | models.Q(failed_attempts=0),
                name="password_login_lock_resets_failures",
            )
        ]

    def __str__(self) -> str:
        return str(self.user)
