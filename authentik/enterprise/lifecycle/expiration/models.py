"""Automatic user expiration: rules that schedule offboardings for inactive users."""

from collections.abc import Collection, Iterator
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import IntegrityError, models, transaction
from django.db.models import OuterRef, Prefetch, Q, QuerySet
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
from authentik.events.activity import (
    EXACT_ACTIVITY_ACTIONS,
    REFRESH_ACTIVITY_INTERVAL,
    load_activity,
    with_activity,
)
from authentik.events.models import Event, EventAction, NotificationSeverity, NotificationTransport
from authentik.lib.models import SerializerModel, SimpleThroughModel
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
from authentik.policies.models import PolicyBinding, PolicyBindingModel

LOGGER = get_logger()

# Users are read in chunks so a large dormant backlog on first enable does not
# load every row into memory.
CANDIDATE_CHUNK_SIZE = 500

# When several rules would expire the same user, the earliest expiration wins. On the
# same date the least destructive action wins, so a rule never deletes a user that
# another rule would only deactivate at that time.
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
    # New rules start disabled so they can be previewed and have policies bound
    # before the first sweep schedules anyone.
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
            if not hasattr(user, "expiration_event_at"):
                load_activity(user)
            event_at = getattr(user, "expiration_event_at", None)
            refresh_at = getattr(user, "expiration_refresh_at", None)
            last_activity = max(
                filter(
                    None,
                    (
                        last_activity,
                        event_at,
                        refresh_at + REFRESH_ACTIVITY_INTERVAL if refresh_at else None,
                    ),
                )
            )
        return last_activity + self.inactivity_timedelta

    def rank(self, user: User) -> Rank:
        """Lower ranks win `user`: the earliest expiration, then the least destructive
        action, then the lowest rule ID so that full ties resolve the same way every time."""
        return (self.due_at(user), ACTION_SEVERITY[self.action], self.pk)

    @staticmethod
    def row_rank(row: UserOffboarding) -> Rank:
        """Rank of the rule that owns `row`, as stored on the row."""
        return (row.scheduled_at, ACTION_SEVERITY[row.action], row.rule_id)

    def _update_offboarding(self, row: UserOffboarding, due_at: datetime):
        """Write this rule's settings onto a locked pending row and make it the owner."""
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
        """Hand a locked, reconciled pending row to the enabled rule that outranks its
        owner, if any. Execution calls this so a lost insert race, or a rule enabled or
        edited since the last sweep, cannot run the wrong action. Returns whether the
        owner changed."""
        best: UserExpirationRule | None = None
        best_rank = cls.row_rank(row)
        for rule in cls.objects.filter(enabled=True).exclude(pk=row.rule_id):
            # Execution preloads activity once, so ranking needs no event queries.
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
            if self.activity_basis == ActivityBasis.SUCCESSFUL_EVENTS:
                recent = Event.objects.filter(
                    user__pk=models.Func(
                        OuterRef("pk"), function="to_jsonb", output_field=models.JSONField()
                    )
                ).filter(
                    Q(action__in=EXACT_ACTIVITY_ACTIONS, created__gt=threshold)
                    | Q(
                        action=EventAction.TOKEN_REFRESH,
                        created__gt=threshold - REFRESH_ACTIVITY_INTERVAL,
                    )
                )
                # Reject recent activity before policies and exact timestamp loads.
                qs = with_activity(qs.exclude(models.Exists(recent)))
        return qs

    def _apply_policies(self, qs: QuerySet[User]) -> QuerySet[User]:
        """Filter `qs` by the rule's policy bindings. Dynamic policies run per user in
        Python, so this is always the last step, on an already narrowed set."""
        if not PolicyBinding.objects.filter(target=self, enabled=True).exists():
            return qs
        from authentik.policies.engine import FilterPolicyEngine

        return FilterPolicyEngine(self, qs).build().result

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
        # Any pending row (manual or generated) excludes the user; one per user is a
        # DB constraint.
        qs = qs.exclude(
            pk__in=UserOffboarding.objects.filter(status=OffboardingStatus.PENDING)
            .exclude(pk__in=withdrawn)
            .values("user")
        )
        # A terminal generated row newer than the user's last login exempts them
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
            executed_at__gte=OuterRef("login_activity"),
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
        transports = list(self.notification_transports.all())
        if not transports:
            # The task uses a transient local transport for in-app-only delivery.
            send_notification.send_with_options(
                args=(None, event.pk, user.pk, NotificationSeverity.NOTICE),
                rel_obj=self,
            )
        for transport in transports:
            send_notification.send_with_options(
                args=(transport.pk, event.pk, user.pk, NotificationSeverity.NOTICE),
                rel_obj=transport,
            )

    def _pending_due_at(self, row: UserOffboarding) -> datetime | None:
        """Re-evaluate an owned row without changing it, assuming the rule is enabled."""
        event_after_creation = False
        if self.activity_basis == ActivityBasis.SUCCESSFUL_EVENTS:
            if not hasattr(row.user, "expiration_event_at"):
                load_activity(row.user)
            event_after_creation = any(
                activity is not None and activity >= row.created_at
                for activity in (
                    getattr(row.user, "expiration_event_at", None),
                    getattr(row.user, "expiration_refresh_at", None),
                )
            )
        if (
            not self._in_scope(row.user)
            or (row.user.last_login is not None and row.user.last_login >= row.created_at)
            or event_after_creation
        ):
            return None
        return self.due_at(row.user)

    def reconcile_offboarding(self, row: UserOffboarding) -> tuple[bool, bool]:
        """Refresh a locked pending row owned by this rule.

        Both the sweep and execution use this, so execution need not wait for a sweep
        to pick up changed settings. Moving a deadline later is silent; moving it
        earlier or changing the action requests another warning. The caller sends it
        after releasing the row lock.

        Returns whether the row was kept and whether another warning is needed.
        """
        due_at = self._pending_due_at(row) if self.enabled else None
        if due_at is None:
            row.delete()
            return False, False
        rewarn = due_at < row.scheduled_at or row.action != self.action
        if (row.scheduled_at, row.action, row.revoke_sessions, row.revoke_tokens) != (
            due_at,
            self.action,
            self.revoke_sessions,
            self.revoke_tokens,
        ):
            self._update_offboarding(row, due_at)
        return True, rewarn

    def _revisit_owned_rows(self):
        """Reconcile only rows this rule still owns after acquiring the row lock."""
        rows = UserOffboarding.objects.filter(
            rule=self, status=OffboardingStatus.PENDING
        ).values_list("pk", flat=True)
        for row_pk in rows.iterator(chunk_size=CANDIDATE_CHUNK_SIZE):
            with transaction.atomic():
                row = (
                    UserOffboarding.objects.select_for_update()
                    .filter(pk=row_pk, rule=self, status=OffboardingStatus.PENDING)
                    .select_related("user")
                    .first()
                )
                if row is None:
                    continue
                _, rewarn = self.reconcile_offboarding(row)
            if rewarn:
                self._warn(row.user, row)

    def _foreign_rows(self) -> QuerySet[UserOffboarding]:
        """Generated pending rows eligible for this rule's tightening pass."""
        return (
            UserOffboarding.objects.filter(status=OffboardingStatus.PENDING, rule__isnull=False)
            .exclude(rule=self)
            .filter(user__in=self.scope(threshold=self._threshold()))
        )

    def preview_pending(self) -> Iterator[tuple[str, UserOffboarding, datetime | None]]:
        """Preview changes to existing rows if enabled, without writing or warning.

        Manual rows and terminal exemptions are never taken over. Like the sweep,
        foreign rows are compared to their stored rank, not their owner's current settings.
        """
        activity = Prefetch("user", queryset=with_activity(User.objects.all()))
        owned = UserOffboarding.objects.filter(rule=self, status=OffboardingStatus.PENDING)
        for row in (
            owned.order_by("user__username")
            .prefetch_related(activity)
            .iterator(chunk_size=CANDIDATE_CHUNK_SIZE)
        ):
            due_at = self._pending_due_at(row)
            if due_at is None:
                yield "removed", row, None
            elif (row.scheduled_at, row.action, row.revoke_sessions, row.revoke_tokens) != (
                due_at,
                self.action,
                self.revoke_sessions,
                self.revoke_tokens,
            ):
                yield "updated", row, due_at
        for row in (
            self._foreign_rows()
            .order_by("user__username")
            .prefetch_related(activity)
            .iterator(chunk_size=CANDIDATE_CHUNK_SIZE)
        ):
            rank = self.rank(row.user)
            if rank < self.row_rank(row) and self._in_scope(row.user):
                yield "taken_over", row, rank[0]

    def _tighten_foreign_rows(self):
        """Tightening pass: take over pending rows of other rules when this rule outranks
        their owner (see `rank`). The user is warned again because date or action changed."""
        rows = self._foreign_rows().select_related("user")
        # Policies run only on the users behind these few rows, not the whole scope.
        passing = self._apply_policies(User.objects.filter(pk__in=rows.values("user")))
        # Fetch activity in a batch rather than querying events for each pending row.
        users = {user.pk: user for user in with_activity(passing)}
        for row in rows.filter(user_id__in=users):
            row.user = users[row.user_id]
            rank = self.rank(row.user)
            with transaction.atomic():
                locked = (
                    UserOffboarding.objects.select_for_update()
                    .filter(pk=row.pk, status=OffboardingStatus.PENDING, rule__isnull=False)
                    .first()
                )
                if locked is None or rank >= self.row_rank(locked):
                    continue
                self._update_offboarding(locked, rank[0])
            self._warn(row.user, locked)

    def apply(self) -> int:
        """Run one sweep. Returns the number of offboardings created."""
        if not self.enabled:
            return 0
        self._revisit_owned_rows()
        self._tighten_foreign_rows()
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
