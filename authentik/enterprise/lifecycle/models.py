from uuid import uuid4

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q, QuerySet
from django.db.models.fields import Field
from django.db.models.functions import Cast
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer

from authentik.blueprints.models import ManagedModel
from authentik.core.models import Group, User
from authentik.enterprise.lifecycle.utils import link_for_model
from authentik.events.models import Event, EventAction, NotificationSeverity, NotificationTransport
from authentik.lib.models import SerializerModel
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator


class LifecycleRule(SerializerModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.TextField(unique=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.TextField(null=True, default=None)
    object = GenericForeignKey("content_type", "object_id")

    interval = models.TextField(
        default="days=60",
        validators=[timedelta_string_validator],
    )
    # Grace period starts after a review is due
    grace_period = models.TextField(
        default="days=30",
        validators=[timedelta_string_validator],
    )

    # The review has to be conducted by `min_reviewers` members of `reviewer_groups`
    # (total or per group depending on `min_reviewers_is_per_group` flag) as well
    # as all of `reviewers`
    reviewer_groups = models.ManyToManyField("authentik_core.Group", blank=True)
    min_reviewers = models.PositiveSmallIntegerField(default=1)
    min_reviewers_is_per_group = models.BooleanField(default=False)
    reviewers = models.ManyToManyField("authentik_core.User", blank=True)

    notification_transports = models.ManyToManyField(
        NotificationTransport,
        help_text=_(
            "Select which transports should be used to notify the reviewers. If none are "
            "selected, the notification will only be shown in the authentik UI."
        ),
        blank=True,
    )

    class Meta:
        indexes = [models.Index(fields=["content_type"])]
        unique_together = [["content_type", "object_id"]]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type"],
                condition=Q(object_id__isnull=True),
                name="uniq_lifecycle_rule_ct_null_object",
            )
        ]

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.lifecycle.api.rules import LifecycleRuleSerializer

        return LifecycleRuleSerializer

    def _get_pk_field(self) -> Field:
        model = self.content_type.model_class()
        pk = model._meta.pk
        while hasattr(pk, "target_field"):
            pk = pk.target_field
        return pk.__class__()

    def get_objects(self) -> QuerySet:
        qs = self.content_type.get_all_objects_for_this_type()
        if self.object_id:
            qs = qs.filter(pk=self.object_id)
        else:
            qs = qs.exclude(
                pk__in=LifecycleRule.objects.filter(
                    content_type=self.content_type, object_id__isnull=False
                ).values_list(Cast("object_id", output_field=self._get_pk_field()), flat=True)
            )
        return qs

    def _get_stale_iterations(self) -> QuerySet[LifecycleIteration]:
        filter = ~Q(content_type=self.content_type)
        if self.object_id:
            filter = filter | ~Q(object_id=self.object_id)
        filter = Q(state__in=(ReviewState.PENDING, ReviewState.OVERDUE)) & filter
        return self.lifecycleiteration_set.filter(filter)

    def _get_newly_overdue_iterations(self) -> QuerySet[LifecycleIteration]:
        return self.lifecycleiteration_set.filter(
            opened_on__lte=timezone.now() - timedelta_from_string(self.grace_period),
            state=ReviewState.PENDING,
        )

    def _get_newly_due_objects(self) -> QuerySet:
        recent_iteration_ids = LifecycleIteration.objects.filter(
            content_type=self.content_type,
            object_id__isnull=False,
            opened_on__gte=timezone.now() - timedelta_from_string(self.interval),
        ).values_list(Cast("object_id", output_field=self._get_pk_field()), flat=True)

        return self.get_objects().exclude(pk__in=recent_iteration_ids)

    def apply(self):
        self._get_stale_iterations().update(state=ReviewState.CANCELED)

        for iteration in self._get_newly_overdue_iterations():
            iteration.make_overdue()

        for obj in self._get_newly_due_objects():
            LifecycleIteration.start(content_type=self.content_type, object_id=obj.pk, rule=self)

    def is_satisfied_for_iteration(self, iteration: LifecycleIteration) -> bool:
        reviewers = self.reviewers.all()
        if (
            iteration.review_set.filter(reviewer__in=reviewers).distinct("reviewer").count()
            < reviewers.count()
        ):
            return False
        if self.reviewer_groups.count() == 0:
            return True
        if self.min_reviewers_is_per_group:
            for g in self.reviewer_groups.all():
                if (
                    iteration.review_set.filter(
                        reviewer__groups__in=Group.objects.filter(pk=g.pk).with_descendants()
                    )
                    .distinct()
                    .count()
                    < self.min_reviewers
                ):
                    return False
            return True
        else:
            return (
                iteration.review_set.filter(
                    reviewer__groups__in=self.reviewer_groups.all().with_descendants()
                )
                .distinct()
                .count()
                >= self.min_reviewers
            )

    def get_reviewers(self) -> QuerySet[User]:
        return User.objects.filter(
            Q(id__in=self.reviewers.all().values_list("pk", flat=True))
            | Q(groups__in=self.reviewer_groups.all().with_descendants())
        ).distinct()

    def notify_reviewers(self, event: Event, severity: str):
        from authentik.enterprise.lifecycle.tasks import send_notification

        for transport in self.notification_transports.all():
            for user in self.get_reviewers():
                send_notification.send_with_options(
                    args=(transport.pk, event.pk, user.pk, severity),
                    rel_obj=transport,
                )
                if transport.send_once:
                    break


class ReviewState(models.TextChoices):
    REVIEWED = "REVIEWED", _("Reviewed")
    PENDING = "PENDING", _("Pending")
    OVERDUE = "OVERDUE", _("Overdue")
    CANCELED = "CANCELED", _("Canceled")


class LifecycleIteration(SerializerModel, ManagedModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.TextField(null=False)
    object = GenericForeignKey("content_type", "object_id")

    rule = models.ForeignKey(LifecycleRule, null=True, on_delete=models.SET_NULL)

    state = models.CharField(max_length=10, choices=ReviewState, default=ReviewState.PENDING)
    opened_on = models.DateField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["content_type", "opened_on"])]

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.lifecycle.api.iterations import LifecycleIterationSerializer

        return LifecycleIterationSerializer

    def _get_model_name(self) -> str:
        return self.content_type.name.lower()

    def _get_event_args(self) -> dict:
        return {
            "target": self.object,
            "hyperlink": link_for_model(self.object),
            "hyperlink_label": _(f"Go to {self._get_model_name()}"),
            "lifecycle_iteration": self.id,
        }

    def initialize(self):
        event = Event.new(
            EventAction.REVIEW_INITIATED,
            message=_(f"Access review is due for {self.content_type.name} {str(self.object)}"),
            **self._get_event_args(),
        )
        event.save()
        self.rule.notify_reviewers(event, NotificationSeverity.NOTICE)

    def make_overdue(self):
        self.state = ReviewState.OVERDUE

        event = Event.new(
            EventAction.REVIEW_OVERDUE,
            message=_(f"Access review is overdue for {self.content_type.name} {str(self.object)}"),
            **self._get_event_args(),
        )
        event.save()
        self.rule.notify_reviewers(event, NotificationSeverity.ALERT)
        self.save()

    @staticmethod
    def start(content_type: ContentType, object_id: str, rule: LifecycleRule) -> LifecycleIteration:
        iteration = LifecycleIteration.objects.create(
            content_type=content_type, object_id=object_id, rule=rule
        )
        iteration.initialize()
        return iteration

    def make_reviewed(self, request: HttpRequest):
        self.state = ReviewState.REVIEWED
        event = Event.new(
            EventAction.REVIEW_COMPLETED,
            message=_(f"Access review completed for {self.content_type.name} {str(self.object)}"),
            **self._get_event_args(),
        ).from_http(request)
        event.save()
        self.rule.notify_reviewers(event, NotificationSeverity.NOTICE)
        self.save()

    def on_review(self, request: HttpRequest):
        if self.state not in (ReviewState.PENDING, ReviewState.OVERDUE):
            raise AssertionError("Review is not pending or overdue")
        if self.rule.is_satisfied_for_iteration(self):
            self.make_reviewed(request)

    def user_can_review(self, user: User) -> bool:
        if self.state not in (ReviewState.PENDING, ReviewState.OVERDUE):
            return False
        if self.review_set.filter(reviewer=user).exists():
            return False
        groups = self.rule.reviewer_groups.all()
        if groups:
            for group in groups:
                if group.is_member(user):
                    return True
            return False
        else:
            return user in self.rule.get_reviewers()


class Review(SerializerModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    iteration = models.ForeignKey(LifecycleIteration, on_delete=models.CASCADE)

    reviewer = models.ForeignKey("authentik_core.User", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(null=True)

    class Meta:
        unique_together = [["iteration", "reviewer"]]

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.lifecycle.api.reviews import ReviewSerializer

        return ReviewSerializer
