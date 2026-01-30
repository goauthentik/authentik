from datetime import timedelta
from uuid import uuid4

from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import QuerySet
from django.db.models.functions import Cast
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer

from authentik.core.models import User
from authentik.events.models import Event, EventAction, NotificationSeverity, NotificationTransport
from authentik.lib.models import SerializerModel


class LifecycleRule(SerializerModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.TextField(null=True, default=None)
    object = GenericForeignKey("content_type", "object_id")

    interval_months = models.SmallIntegerField(default=1)
    # Grace period starts after a review is due
    grace_period_days = models.SmallIntegerField(default=28)

    # The review can be conducted by either `min_reviewers` members of `reviewer_groups`
    # or all of `reviewers`
    reviewer_groups = models.ManyToManyField("authentik_core.Group", blank=True)
    min_reviewers = models.PositiveSmallIntegerField(default=1)
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
        unique_together = ("content_type", "object_id")
        indexes = [models.Index(fields=["content_type"])]

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.reviews.api.lifecycle_rules import LifecycleRuleSerializer

        return LifecycleRuleSerializer

    def get_reviews(self):
        qs = Review.objects.filter(content_type=self.content_type)
        if self.object_id:
            qs = qs.filter(object_id=self.object_id)
        else:
            qs = qs.exclude(
                object_id__in=LifecycleRule.object.filter(
                    content_type=self.content_type
                ).values_list("object_id", flat=True)
            )
        return qs

    def get_objects(self):
        qs = self.content_type.get_all_objects_for_this_type()
        if self.object_id:
            qs = qs.filter(pk=self.object_id)
        else:
            qs = qs.exclude(
                pk__in=LifecycleRule.object.filter(content_type=self.content_type).values_list(
                    "object_id", flat=True
                )
            )
        return qs

    def _get_newly_overdue_reviews(self) -> QuerySet[Review]:
        return self.get_reviews().filter(
            opened_on__lte=timezone.now() - timedelta(days=self.grace_period_days),
            state=ReviewState.PENDING,
        )

    def _get_newly_due_objects(self) -> QuerySet:
        model = self.content_type.model_class()
        pk = model._meta.pk
        while hasattr(pk, "target_field"):
            pk = pk.target_field
        pk_output_field = pk.__class__()

        recent_review_ids = Review.objects.filter(
            content_type=self.content_type,
            opened_on__gte=timezone.now() - relativedelta(months=self.interval_months),
        ).values_list(Cast("object_id", output_field=pk_output_field), flat=True)

        return self.get_objects().exclude(pk__in=recent_review_ids)

    def apply(self):
        for review in self._get_newly_overdue_reviews():
            review.make_overdue()

        for obj in self._get_newly_due_objects():
            Review.start(content_type=self.content_type, object_id=obj.pk)

    def is_satisfied_for_review(self, review: Review) -> bool:
        reviewers = list(self.reviewers.all())
        if reviewers:
            return review.attestation_set.filter(reviewer__in=reviewers).distinct(
                "reviewer"
            ).count() == len(reviewers)
        else:
            return review.attestation_set.distinct("reviewer").count() >= self.min_reviewers

    def get_reviewers(self) -> list[User]:
        return list(self.reviewers.all()) or list(
            User.objects.filter(ak_groups__in=self.reviewer_groups.all())
        )

    def notify_reviewers(self, event: Event, severity: str):
        from authentik.enterprise.reviews.tasks import send_notification

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


class Review(SerializerModel):
    id = models.UUIDField(primary_key=True, default=uuid4, null=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.TextField(null=False)
    object = GenericForeignKey("content_type", "object_id")

    state = models.CharField(max_length=10, choices=ReviewState, default=ReviewState.PENDING)
    opened_on = models.DateField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["content_type", "opened_on"])]

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.reviews.api.reviews import ReviewSerializer

        return ReviewSerializer

    @property
    def rule(self) -> LifecycleRule:
        try:
            return LifecycleRule.objects.get(
                content_type=self.content_type, object_id=self.object_id
            )
        except LifecycleRule.DoesNotExist:
            return LifecycleRule(content_type=self.content_type)

    def initialize(self):
        event = Event.new(
            EventAction.REVIEW_INITIATED,
            target=self,
            message=_(f"Access review is due for {self.content_type.name} {str(self.object)}"),
            # TODO:hyperlink
        )
        event.save()
        self.rule.notify_reviewers(event, NotificationSeverity.NOTICE)

    def make_overdue(self):
        self.state = ReviewState.OVERDUE

        event = Event.new(
            EventAction.REVIEW_OVERDUE,
            target=self,
            message=_(f"Access review is overdue for {self.content_type.name} {str(self.object)}"),
            # TODO:hyperlink
        )
        event.save()

        # TODO: notifications?
        self.save()

    @staticmethod
    def start(content_type: ContentType, object_id: str) -> Review:
        review = Review.objects.create(content_type=content_type, object_id=object_id)
        review.initialize()
        return review

    def make_reviewed(self):
        self.state = ReviewState.REVIEWED
        # TODO: store user and http context
        event = Event.new(
            EventAction.REVIEW_COMPLETED,
            target=self,
            message=_(f"Access review completed for {self.content_type.name} {str(self.object)}"),
            # TODO:hyperlink
        )
        event.save()
        self.rule.notify_reviewers(event, NotificationSeverity.NOTICE)
        self.save()

    def on_attestation(self):
        assert self.state in (ReviewState.PENDING, ReviewState.OVERDUE)
        if self.rule.is_satisfied_for_review(self):
            self.make_reviewed()


class Attestation(SerializerModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    reviewer = models.ForeignKey("authentik_core.User", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(null=True)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.reviews.api.attestations import AttestationSerializer

        return AttestationSerializer

    def save(self, *args, **kwargs):
        creating = self.pk is None or kwargs.get("force_insert", False)
        super().save(*args, **kwargs)
        if creating:
            self.review.on_attestation()
