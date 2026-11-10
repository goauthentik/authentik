"""Automatic user expiration: rules that schedule offboardings for inactive users."""

from collections.abc import Collection, Iterator
from datetime import datetime, timedelta
from itertools import batched
from uuid import UUID, uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import IntegrityError, models, transaction
from django.db.models import OuterRef, Prefetch, Q, QuerySet
from django.db.models.functions import Greatest
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.core.models import USER_ACTIVITY_INTERVAL, Group, User, UserTypes
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

CHUNK_SIZE = 500
ACTION_SEVERITY = {OffboardingAction.DEACTIVATE: 0, OffboardingAction.DELETE: 1}

type Rank = tuple[datetime, int, UUID]


def default_user_types() -> list[str]:
    return [UserTypes.INTERNAL, UserTypes.EXTERNAL]


class ActivityBasis(models.TextChoices):
    LAST_LOGIN = "last_login", _("Last login")
    SUCCESSFUL_EVENTS = "successful_events", _("Last activity")


class UserExpirationRule(SerializerModel, PolicyBindingModel):
    """Schedule an offboarding for every user in scope who has been inactive for
    `inactivity_duration`, using the selected activity clock."""

    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.TextField(unique=True)
    # Disabled by default so rules can be previewed before the first sweep.
    enabled = models.BooleanField(default=False)
    activity_basis = models.TextField(
        choices=ActivityBasis.choices,
        default=ActivityBasis.SUCCESSFUL_EVENTS,
        help_text=_("Measure inactivity from the last login or successful user activity."),
    )
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
        help_text=_("Only expire users of these types. Service accounts are excluded by default."),
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

    def due_at(self, user: User) -> datetime:
        last_activity = max(filter(None, (user.last_login, user.date_joined)))
        if self.activity_basis == ActivityBasis.SUCCESSFUL_EVENTS:
            activity = getattr(user, "activity", None)
            if activity is not None:
                last_activity = max(
                    last_activity, activity.last_activity_at + USER_ACTIVITY_INTERVAL
                )
        return last_activity + self.inactivity_timedelta

    def rank(self, user: User) -> Rank:
        """Lowest wins: earliest due date, then least destructive action, then rule ID."""
        return (self.due_at(user), ACTION_SEVERITY[self.action], self.pk)

    @staticmethod
    def row_rank(row: UserOffboarding) -> Rank:
        return (row.scheduled_at, ACTION_SEVERITY[row.action], row.rule_id)

    @staticmethod
    def withdraw_pending(user: User, logged_in_at: datetime | None = None):
        """Delete the user's pending generated offboardings, optionally only those
        created before `logged_in_at`."""
        rows = UserOffboarding.objects.filter(
            user=user, rule__isnull=False, status=OffboardingStatus.PENDING
        )
        if logged_in_at is not None:
            rows = rows.filter(created_at__lte=logged_in_at)
        rows.delete()

    def _row_matches(self, row: UserOffboarding, due_at: datetime) -> bool:
        return (row.scheduled_at, row.action, row.revoke_sessions, row.revoke_tokens) == (
            due_at,
            self.action,
            self.revoke_sessions,
            self.revoke_tokens,
        )

    def _update_offboarding(self, row: UserOffboarding, due_at: datetime):
        row.rule = self
        row.scheduled_at = due_at
        row.action = self.action
        row.revoke_sessions = self.revoke_sessions
        row.revoke_tokens = self.revoke_tokens
        row.save(
            update_fields=["rule", "scheduled_at", "action", "revoke_sessions", "revoke_tokens"]
        )

    @classmethod
    def resolve_winner(cls, row: UserOffboarding) -> bool:
        """Hand a locked pending row to the enabled rule that outranks its owner, if any.
        Returns whether the owner changed."""
        best: UserExpirationRule | None = None
        best_rank = cls.row_rank(row)
        for rule in cls.objects.filter(enabled=True).exclude(pk=row.rule_id):
            rank = rule.rank(row.user)
            if rank < best_rank and rule._in_scope(row.user):
                best, best_rank = rule, rank
        if best is None:
            return False
        best._update_offboarding(row, best_rank[0])
        return True

    def scope(
        self, *, threshold: datetime | None = None, user: User | None = None
    ) -> QuerySet[User]:
        """Users this rule applies to, before policies. With `threshold`, only users
        inactive since then."""
        types = [t for t in self.user_types if t != UserTypes.INTERNAL_SERVICE_ACCOUNT]
        qs = (
            User.objects.exclude_anonymous()
            .select_related("activity")
            .filter(is_active=True, type__in=types)
        )
        if user is not None:
            qs = qs.filter(pk=user.pk)
        if self.group_id:
            members = Group.objects.filter(pk=self.group_id).with_descendants()
            qs = qs.filter(pk__in=User.objects.filter(groups__in=members).values("pk"))
        if self.exclude_superusers:
            superuser_groups = Group.objects.filter(is_superuser=True).with_descendants()
            qs = qs.exclude(pk__in=User.objects.filter(groups__in=superuser_groups).values("pk"))
        if threshold is not None:
            # Two range tests instead of GREATEST() so the last_login index is used.
            qs = qs.filter(
                Q(last_login__isnull=True) | Q(last_login__lte=threshold),
                date_joined__lte=threshold,
            )
            if self.activity_basis == ActivityBasis.SUCCESSFUL_EVENTS:
                qs = qs.filter(
                    Q(activity__isnull=True)
                    | Q(activity__last_activity_at__lte=threshold - USER_ACTIVITY_INTERVAL)
                )
        return qs

    def _apply_policies(self, qs: QuerySet[User]) -> QuerySet[User]:
        """Policies run per user, so only apply them to an already narrowed set."""
        if not PolicyBinding.objects.filter(target=self, enabled=True).exists():
            return qs
        from authentik.policies.engine import FilterPolicyEngine

        return FilterPolicyEngine(self, qs).build().result

    def _eligible_user_ids(self, user_ids: Collection[int]) -> set[int]:
        return set(
            self._apply_policies(self.scope().filter(pk__in=user_ids)).values_list("pk", flat=True)
        )

    def _in_scope(self, user: User) -> bool:
        return self._apply_policies(self.scope(user=user)).exists()

    def _threshold(self) -> datetime:
        warn = timedelta_from_string(self.warn_before) if self.warn_before else timedelta()
        return timezone.now() - self.inactivity_timedelta + warn

    def candidates(self, *, withdrawn: Collection[UUID] = ()) -> QuerySet[User]:
        """Users this rule would schedule a new offboarding for on its next run."""
        qs = self.scope(threshold=self._threshold()).annotate(
            login_activity=Greatest("last_login", "date_joined")
        )
        pending = UserOffboarding.objects.filter(
            user=OuterRef("pk"), status=OffboardingStatus.PENDING
        ).exclude(pk__in=withdrawn)
        qs = qs.exclude(models.Exists(pending))
        # Canceled, completed or failed generated rows exempt the user until they
        # log in again.
        terminal = UserOffboarding.objects.filter(
            user=OuterRef("pk"),
            rule__isnull=False,
            status__in=[
                OffboardingStatus.COMPLETED,
                OffboardingStatus.CANCELED,
                OffboardingStatus.FAILED,
            ],
            executed_at__gte=OuterRef("login_activity"),
        )
        qs = qs.exclude(models.Exists(terminal))
        return self._apply_policies(qs)

    def _warn(self, user: User, offboarding: UserOffboarding):
        if not self.warn_before:
            return

        from authentik.enterprise.lifecycle.review.tasks import send_notification

        event = Event.new(
            EventAction.USER_EXPIRATION_WARNING,
            message=gettext(
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
        transports = list(self.notification_transports.all())
        if not transports:
            send_notification.send_with_options(
                args=(None, event.pk, user.pk, NotificationSeverity.NOTICE),
                rel_obj=self,
            )
        for transport in transports:
            send_notification.send_with_options(
                args=(transport.pk, event.pk, user.pk, NotificationSeverity.NOTICE),
                rel_obj=transport,
            )

    def _pending_due_at(
        self, row: UserOffboarding, *, in_scope: bool | None = None
    ) -> datetime | None:
        """Due date for an owned row, or None if it should be withdrawn, assuming the rule
        is enabled."""
        if in_scope is None:
            in_scope = self._in_scope(row.user)
        activity = getattr(row.user, "activity", None)
        event_after_creation = (
            self.activity_basis == ActivityBasis.SUCCESSFUL_EVENTS
            and activity is not None
            and activity.last_activity_at >= row.created_at
        )
        if (
            not in_scope
            or (row.user.last_login is not None and row.user.last_login >= row.created_at)
            or event_after_creation
        ):
            return None
        return self.due_at(row.user)

    def reconcile_offboarding(
        self, row: UserOffboarding, *, in_scope: bool | None = None
    ) -> tuple[bool, bool]:
        """Refresh a locked pending row owned by this rule. Returns whether the row was
        kept and whether the user needs another warning."""
        due_at = self._pending_due_at(row, in_scope=in_scope) if self.enabled else None
        if due_at is None:
            row.delete()
            return False, False
        rewarn = due_at < row.scheduled_at or row.action != self.action
        if not self._row_matches(row, due_at):
            self._update_offboarding(row, due_at)
        return True, rewarn

    def _revisit_owned_rows(self):
        rows = UserOffboarding.objects.filter(
            rule=self, status=OffboardingStatus.PENDING
        ).select_related("user", "user__activity")
        for batch in batched(rows.iterator(chunk_size=CHUNK_SIZE), CHUNK_SIZE, strict=False):
            eligible = (
                self._eligible_user_ids([row.user_id for row in batch]) if self.enabled else set()
            )
            for row in batch:
                due_at = (
                    self._pending_due_at(row, in_scope=row.user_id in eligible)
                    if self.enabled
                    else None
                )
                if due_at is not None and self._row_matches(row, due_at):
                    continue
                # Re-read changed rows under the lock before reconciling them.
                with transaction.atomic():
                    locked = (
                        UserOffboarding.objects.select_for_update(of=("self",))
                        .filter(pk=row.pk, rule=self, status=OffboardingStatus.PENDING)
                        .select_related("user", "user__activity")
                        .first()
                    )
                    if locked is None:
                        continue
                    _, rewarn = self.reconcile_offboarding(
                        locked, in_scope=locked.user_id in eligible
                    )
                if rewarn:
                    self._warn(locked.user, locked)

    def _foreign_rows(self) -> QuerySet[UserOffboarding]:
        return (
            UserOffboarding.objects.filter(status=OffboardingStatus.PENDING, rule__isnull=False)
            .exclude(rule=self)
            .filter(user__in=self.scope(threshold=self._threshold()))
        )

    def preview_pending(self) -> Iterator[tuple[str, UserOffboarding, datetime | None]]:
        """Changes to pending rows if this rule were enabled, without writing anything."""
        activity = Prefetch("user", queryset=User.objects.select_related("activity"))
        owned = UserOffboarding.objects.filter(rule=self, status=OffboardingStatus.PENDING)
        owned_rows = owned.order_by("user__username").prefetch_related(activity)
        for batch in batched(owned_rows.iterator(chunk_size=CHUNK_SIZE), CHUNK_SIZE, strict=False):
            eligible = self._eligible_user_ids([row.user_id for row in batch])
            for row in batch:
                due_at = self._pending_due_at(row, in_scope=row.user_id in eligible)
                if due_at is None:
                    yield "removed", row, None
                elif not self._row_matches(row, due_at):
                    yield "updated", row, due_at
        for batch in batched(
            self._foreign_rows()
            .order_by("user__username")
            .prefetch_related(activity)
            .iterator(chunk_size=CHUNK_SIZE),
            CHUNK_SIZE,
            strict=False,
        ):
            ranked = [(row, self.rank(row.user)) for row in batch]
            ranked = [(row, rank) for row, rank in ranked if rank < self.row_rank(row)]
            if not ranked:
                continue
            eligible = self._eligible_user_ids([row.user_id for row, _ in ranked])
            for row, rank in ranked:
                if row.user_id in eligible:
                    yield "taken_over", row, rank[0]

    def _tighten_foreign_rows(self):
        """Take over other rules' pending rows that this rule outranks."""
        rows = self._foreign_rows().select_related("user", "user__activity")
        for batch in batched(rows.iterator(chunk_size=CHUNK_SIZE), CHUNK_SIZE, strict=False):
            ranked = [(row, self.rank(row.user)) for row in batch]
            ranked = [(row, rank) for row, rank in ranked if rank < self.row_rank(row)]
            if not ranked:
                continue
            eligible = self._eligible_user_ids([row.user_id for row, _ in ranked])
            for row, rank in ranked:
                if row.user_id not in eligible:
                    continue
                with transaction.atomic():
                    locked = (
                        UserOffboarding.objects.select_for_update(of=("self",))
                        .filter(pk=row.pk, status=OffboardingStatus.PENDING, rule__isnull=False)
                        .first()
                    )
                    if locked is None or rank >= self.row_rank(locked):
                        continue
                    self._update_offboarding(locked, rank[0])
                self._warn(row.user, locked)

    def apply(self) -> int:
        """Run one sweep. Returns the number of offboardings created."""
        self._revisit_owned_rows()
        if not self.enabled:
            return 0
        self._tighten_foreign_rows()
        created = 0
        candidates = self.candidates().iterator(chunk_size=CHUNK_SIZE)
        for batch in batched(candidates, CHUNK_SIZE, strict=False):
            # Activity may have changed since candidates were selected.
            still_inactive = set(
                self.scope(threshold=self._threshold())
                .filter(pk__in=[user.pk for user in batch])
                .values_list("pk", flat=True)
            )
            for user in batch:
                if user.pk not in still_inactive:
                    continue
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
                    # Another offboarding was scheduled since selection.
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
