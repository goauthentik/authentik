from uuid import uuid4

from django.db import models, transaction
from django.db.models import Q
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer

from authentik.lib.models import SerializerModel


class OffboardingAction(models.TextChoices):
    """Action to take against a user when their offboarding is due.

    Designed to grow a `target_state` style action once user state/status lands."""

    DEACTIVATE = "deactivate", _("Deactivate")
    DELETE = "delete", _("Delete")


class OffboardingStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")
    CANCELED = "canceled", _("Canceled")


class UserOffboarding(SerializerModel):
    """Scheduled deactivation/deletion of a single user at an absolute point in time."""

    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.ForeignKey(
        "authentik_core.User", on_delete=models.CASCADE, related_name="offboardings"
    )
    scheduled_at = models.DateTimeField(
        help_text=_("Absolute time at which the offboarding action is executed.")
    )
    action = models.TextField(
        choices=OffboardingAction.choices, default=OffboardingAction.DEACTIVATE
    )
    revoke_sessions = models.BooleanField(
        default=True, help_text=_("Revoke all of the user's sessions when offboarding.")
    )
    revoke_tokens = models.BooleanField(
        default=True, help_text=_("Revoke all of the user's tokens when offboarding.")
    )

    status = models.TextField(choices=OffboardingStatus.choices, default=OffboardingStatus.PENDING)
    created_by = models.ForeignKey(
        "authentik_core.User", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, default=None)
    attempts = models.PositiveSmallIntegerField(
        default=0, help_text=_("Number of times execution has been attempted and failed.")
    )

    class Meta:
        verbose_name = _("User Offboarding")
        verbose_name_plural = _("User Offboardings")
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status=OffboardingStatus.PENDING),
                name="unique_pending_offboarding_per_user",
            )
        ]
        indexes = [
            # The sweeper only scans pending rows by scheduled_at; a partial
            # index keeps this small as terminal (completed/failed/cancelled)
            # rows accumulate as audit records.
            models.Index(
                fields=["scheduled_at"],
                condition=Q(status=OffboardingStatus.PENDING),
                name="pending_offboarding_idx",
            )
        ]

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.lifecycle.offboarding.api import UserOffboardingSerializer

        return UserOffboardingSerializer

    def __str__(self):
        return f"User offboarding for user {self.user_id} ({self.action}) at {self.scheduled_at}"

    def cancel(self) -> bool:
        """Cancel iff still pending; returns whether it was cancelled.

        Locked and re-checked under the lock so a concurrent execution can't have
        its terminal status clobbered. The save() emits the audit event.
        """
        with transaction.atomic():
            locked = (
                UserOffboarding.objects.select_for_update()
                .filter(pk=self.pk, status=OffboardingStatus.PENDING)
                .first()
            )
            if locked is None:
                return False
            locked.status = OffboardingStatus.CANCELED
            locked.executed_at = timezone.now()
            locked.save(update_fields=["status", "executed_at"])
        self.status = locked.status
        self.executed_at = locked.executed_at
        return True

    def execute(self, request: HttpRequest | None = None):
        """Run the offboarding action and record the outcome.

        Revocations, the destructive action, and the status write run in one
        transaction, so a mid-way failure rolls back completely: the user is
        left untouched and the row stays `PENDING` for retry.
        """
        from authentik.enterprise.lifecycle.offboarding.actions import offboard_user

        # `delete` removes this row via cascade, so capture the action first.
        is_delete = self.action == OffboardingAction.DELETE
        with transaction.atomic():
            offboard_user(
                self.user,
                self.action,
                revoke_sessions=self.revoke_sessions,
                revoke_tokens=self.revoke_tokens,
                request=request,
                initiator=self.created_by,
            )
            if is_delete:
                return
            self.status = OffboardingStatus.COMPLETED
            self.executed_at = timezone.now()
            self.save(update_fields=["status", "executed_at"])
