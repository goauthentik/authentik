"""Automatic user expiration: rules that schedule offboardings for inactive users."""

from datetime import datetime, timedelta
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import IntegrityError, models, transaction
from django.db.models import OuterRef, Q, QuerySet
from django.db.models.functions import Greatest
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.core.models import Group, User, UserTypes
from authentik.enterprise.lifecycle.offboarding.models import (
    OffboardingAction,
    OffboardingStatus,
    UserOffboarding,
)
from authentik.events.models import Event, EventAction, NotificationSeverity, NotificationTransport
from authentik.lib.models import SerializerModel, SimpleThroughModel
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
from authentik.policies.models import PolicyBinding, PolicyBindingModel

LOGGER = get_logger()

# Users are read in chunks so a large dormant backlog on first enable does not
# load every row into memory.
CANDIDATE_CHUNK_SIZE = 500


def default_user_types() -> list[str]:
    return [UserTypes.INTERNAL, UserTypes.EXTERNAL]


class UserExpirationRule(SerializerModel, PolicyBindingModel):
    """Schedule an offboarding for every user in scope who has been inactive for
    `inactivity_duration`. Inactivity is measured from the later of `last_login`
    and `date_joined`."""

    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.TextField(unique=True)
    enabled = models.BooleanField(default=True)
    group = models.ForeignKey(
        "authentik_core.Group",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        help_text=_(
            "Only expire members of this group (including descendant groups). "
            "Leave empty to apply to every user."
        ),
    )
    user_types = ArrayField(
        models.TextField(choices=UserTypes.choices),
        default=default_user_types,
        blank=True,
        help_text=_(
            "Only expire users of these types. Service accounts authenticate with tokens, "
            "which does not count as activity, so they are excluded by default."
        ),
    )
    inactivity_duration = models.TextField(
        default="days=90",
        validators=[timedelta_string_validator],
        help_text=_("How long a user may be inactive before they are expired."),
    )
    action = models.TextField(
        choices=OffboardingAction.choices, default=OffboardingAction.DEACTIVATE
    )
    revoke_sessions = models.BooleanField(default=True)
    revoke_tokens = models.BooleanField(default=True)
    warn_before = models.TextField(
        null=True,
        blank=True,
        default=None,
        validators=[timedelta_string_validator],
        help_text=_(
            "Schedule the offboarding and notify the user this long before they expire. "
            "Leave empty to expire users without warning."
        ),
    )
    notification_transports = models.ManyToManyField(
        NotificationTransport,
        blank=True,
        through="UserExpirationRuleNotificationTransport",
        help_text=_(
            "Select which transports should be used to warn the user. If none are "
            "selected, the notification will only be shown in the authentik UI."
        ),
    )
    exclude_superusers = models.BooleanField(
        default=True,
        help_text=_("Never expire members of a superuser group."),
    )

    class Meta:
        verbose_name = _("User Expiration Rule")
        verbose_name_plural = _("User Expiration Rules")

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.lifecycle.expiration.api import UserExpirationRuleSerializer

        return UserExpirationRuleSerializer

    def __str__(self):
        return f"User Expiration Rule {self.name}"

    @property
    def inactivity_timedelta(self) -> timedelta:
        return timedelta_from_string(self.inactivity_duration)

    @property
    def warn_timedelta(self) -> timedelta:
        if not self.warn_before:
            return timedelta()
        return timedelta_from_string(self.warn_before)

    @staticmethod
    def last_activity(user: User) -> datetime:
        return max(filter(None, (user.last_login, user.date_joined)))

    def due_at(self, user: User) -> datetime:
        return self.last_activity(user) + self.inactivity_timedelta

    def scope(
        self, *, threshold: datetime | None = None, user: User | None = None
    ) -> QuerySet[User]:
        """Users this rule applies to, before policies. Pure SQL, so it is cheap to
        evaluate over the whole population. With `threshold`, only users whose last
        activity is at or before it. With `user`, narrowed to that user."""
        types = [t for t in self.user_types if t != UserTypes.INTERNAL_SERVICE_ACCOUNT]
        qs = User.objects.filter(is_active=True, type__in=types)
        if user is not None:
            qs = qs.filter(pk=user.pk)
        if self.group_id:
            members = Group.objects.filter(pk=self.group_id).with_descendants()
            qs = qs.filter(pk__in=User.objects.filter(groups__in=members).values("pk"))
        if self.exclude_superusers:
            superuser_groups = Group.objects.filter(is_superuser=True).with_descendants()
            qs = qs.exclude(pk__in=User.objects.filter(groups__in=superuser_groups).values("pk"))
        if threshold is not None:
            # Written as two range tests (not GREATEST()) so the last_login index is used.
            qs = qs.filter(
                Q(last_login__isnull=True) | Q(last_login__lte=threshold),
                date_joined__lte=threshold,
            )
        return qs

    def _apply_policies(self, qs: QuerySet[User]) -> QuerySet[User]:
        """Filter `qs` by the rule's policy bindings. Dynamic policies run per user in
        Python, so this is always the last step, on an already narrowed set."""
        if not PolicyBinding.objects.filter(target=self, enabled=True).exists():
            return qs
        from authentik.policies.engine import FilterPolicyEngine

        return FilterPolicyEngine(self, qs).build().result

    def _in_scope(self, user: User, *, threshold: datetime | None = None) -> bool:
        return self._apply_policies(self.scope(threshold=threshold, user=user)).exists()

    def _threshold(self) -> datetime:
        return timezone.now() - self.inactivity_timedelta + self.warn_timedelta

    def qualifies(self, user: User) -> bool:
        """Whether this rule should expire `user` right now: enabled, in scope, past the
        threshold and passing policies. `candidates()` is this predicate as a queryset,
        minus users who already have a pending or newer terminal offboarding."""
        if not self.enabled:
            return False
        return self._in_scope(user, threshold=self._threshold())

    def candidates(self) -> QuerySet[User]:
        """Users this rule would schedule a new offboarding for on its next run."""
        qs = self.scope(threshold=self._threshold()).annotate(
            last_activity=Greatest("last_login", "date_joined")
        )
        # Any pending row (manual or generated) excludes the user; one per user is a
        # DB constraint.
        qs = qs.exclude(
            pk__in=UserOffboarding.objects.filter(status=OffboardingStatus.PENDING).values("user")
        )
        # A terminal generated row newer than the user's last activity exempts them
        # until they log in again: cancel is an exemption, a reactivated user is not
        # re-expired the next hour, and a failed row is not retried in a loop.
        terminal = UserOffboarding.objects.filter(
            user=OuterRef("pk"),
            rule__isnull=False,
            status__in=[
                OffboardingStatus.COMPLETED,
                OffboardingStatus.CANCELED,
                OffboardingStatus.FAILED,
            ],
            executed_at__gte=OuterRef("last_activity"),
        )
        qs = qs.exclude(models.Exists(terminal))
        return self._apply_policies(qs)

    def _warn(self, user: User, offboarding: UserOffboarding):
        from authentik.enterprise.lifecycle.review.tasks import send_notification

        event = Event.new(
            EventAction.USER_EXPIRATION_WARNING,
            message=_(
                "User %(username)s will be offboarded (%(action)s) on %(scheduled_at)s "
                "due to inactivity"
            )
            % {
                "username": user.username,
                "action": offboarding.action,
                "scheduled_at": offboarding.scheduled_at.isoformat(),
            },
            rule=self,
            scheduled_at=offboarding.scheduled_at,
            offboarding_action=offboarding.action,
        )
        event.set_user(user)
        event.save()
        for transport in self.notification_transports.all():
            send_notification.send_with_options(
                args=(transport.pk, event.pk, user.pk, NotificationSeverity.NOTICE),
                rel_obj=transport,
            )

    def _revisit_owned_rows(self):
        """Loosening pass: push out or delete pending rows this rule owns whose user no
        longer qualifies, or whose due date moved later. Silent, since "later than
        promised" breaks no promise."""
        rows = UserOffboarding.objects.filter(
            rule=self, status=OffboardingStatus.PENDING
        ).select_related("user")
        for row in rows:
            if not self._in_scope(row.user):
                row.delete()
                continue
            due_at = self.due_at(row.user)
            if due_at > row.scheduled_at:
                UserOffboarding.objects.filter(pk=row.pk, status=OffboardingStatus.PENDING).update(
                    scheduled_at=due_at
                )

    def _tighten_foreign_rows(self, threshold: datetime):
        """Tightening pass: take over pending rows of other rules when this rule would
        expire the user earlier. The user is warned again because date and action changed."""
        rows = (
            UserOffboarding.objects.filter(status=OffboardingStatus.PENDING, rule__isnull=False)
            .exclude(rule=self)
            .filter(user__in=self.scope(threshold=threshold))
            .select_related("user")
        )
        # Policies run only on the users behind these few rows, not the whole scope.
        passing = self._apply_policies(User.objects.filter(pk__in=rows.values("user")))
        for row in rows.filter(user__in=passing):
            due_at = self.due_at(row.user)
            with transaction.atomic():
                locked = (
                    UserOffboarding.objects.select_for_update()
                    .filter(pk=row.pk, status=OffboardingStatus.PENDING, scheduled_at__gt=due_at)
                    .first()
                )
                if locked is None:
                    continue
                locked.rule = self
                locked.scheduled_at = due_at
                locked.action = self.action
                locked.revoke_sessions = self.revoke_sessions
                locked.revoke_tokens = self.revoke_tokens
                locked.save(
                    update_fields=[
                        "rule",
                        "scheduled_at",
                        "action",
                        "revoke_sessions",
                        "revoke_tokens",
                    ]
                )
            self._warn(row.user, locked)

    def apply(self) -> int:
        """Run one sweep. Returns the number of offboardings created."""
        if not self.enabled:
            return 0
        self._revisit_owned_rows()
        self._tighten_foreign_rows(self._threshold())
        created = 0
        for user in self.candidates().iterator(chunk_size=CANDIDATE_CHUNK_SIZE):
            try:
                with transaction.atomic():
                    offboarding = UserOffboarding.objects.create(
                        user=user,
                        rule=self,
                        scheduled_at=self.due_at(user),
                        action=self.action,
                        revoke_sessions=self.revoke_sessions,
                        revoke_tokens=self.revoke_tokens,
                    )
            except IntegrityError:
                # A manual offboarding was scheduled between selection and insert.
                continue
            self._warn(user, offboarding)
            created += 1
        LOGGER.info("Applied user expiration rule", rule=self.name, created=created)
        return created


class UserExpirationRuleNotificationTransport(SimpleThroughModel):
    user_expiration_rule = models.ForeignKey(
        UserExpirationRule,
        on_delete=models.CASCADE,
        db_column="userexpirationrule_id",
    )
    notification_transport = models.ForeignKey(
        NotificationTransport, on_delete=models.CASCADE, db_column="notificationtransport_id"
    )

    class Meta:
        db_table = "authentik_lifecycle_userexpirationrule_notification_transports"
        unique_together = (("user_expiration_rule", "notification_transport"),)
        verbose_name = _("User Expiration Rule Notification Transport")
        verbose_name_plural = _("User Expiration Rule Notification Transports")

    def __str__(self):
        return (
            "UserExpirationRuleNotificationTransport for UserExpirationRule "
            f"{self.user_expiration_rule_id} "
            f"and NotificationTransport {self.notification_transport_id}."
        )
