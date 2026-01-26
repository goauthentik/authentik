from datetime import timedelta
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.reviews.models import Attestation, LifecycleRule, Review, ReviewState
from authentik.events.models import (
    Event,
    EventAction,
    NotificationSeverity,
    NotificationTransport,
)
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


class TestReviewModels(TestCase):
    """Tests for access review models."""

    def _create_object(self, model):
        if model is Application:
            return Application.objects.create(name=generate_id(), slug=generate_id())
        if model is Role:
            return Role.objects.create(name=generate_id())
        if model is Group:
            return Group.objects.create(name=generate_id())
        raise AssertionError(f"Unsupported model {model}")

    def _create_rule_for_object(self, obj, **kwargs) -> LifecycleRule:
        content_type = ContentType.objects.get_for_model(obj)
        return LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(obj.pk),
            **kwargs,
        )

    def test_review_start_supported_objects(self):
        """Ensure reviews can be started for applications, roles, and groups."""
        for model in (Application, Role, Group):
            with self.subTest(model=model.__name__):
                obj = self._create_object(model)
                self._create_rule_for_object(obj)
                content_type = ContentType.objects.get_for_model(obj)

                before_events = Event.objects.filter(
                    action=EventAction.REVIEW_INITIATED
                ).count()
                review = Review.start(content_type=content_type, object_id=str(obj.pk))

                self.assertEqual(review.state, ReviewState.PENDING)
                self.assertEqual(review.object, obj)
                self.assertEqual(
                    Event.objects.filter(action=EventAction.REVIEW_INITIATED).count(),
                    before_events + 1,
                )

    def test_attestation_requires_all_explicit_reviewers(self):
        """Explicit reviewers require a full set of attestations to complete the review."""
        obj = Group.objects.create(name=generate_id())
        rule = self._create_rule_for_object(obj)
        reviewer_one = create_test_user()
        reviewer_two = create_test_user()
        rule.reviewers.add(reviewer_one, reviewer_two)

        content_type = ContentType.objects.get_for_model(obj)
        review = Review.start(content_type=content_type, object_id=str(obj.pk))

        Attestation.objects.create(review=review, reviewer=reviewer_one)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.PENDING)

        Attestation.objects.create(review=review, reviewer=reviewer_two)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.REVIEWED)
        self.assertTrue(Event.objects.filter(action=EventAction.REVIEW_COMPLETED).exists())

    def test_attestation_min_reviewers_from_groups(self):
        """Group-based reviews complete once the minimum number of reviewers attest."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj, min_reviewers=2)

        reviewer_group = Group.objects.create(name=generate_id())
        reviewer_one = create_test_user()
        reviewer_two = create_test_user()
        reviewer_group.users.add(reviewer_one, reviewer_two)
        rule.reviewer_groups.add(reviewer_group)

        content_type = ContentType.objects.get_for_model(obj)
        review = Review.start(content_type=content_type, object_id=str(obj.pk))

        Attestation.objects.create(review=review, reviewer=reviewer_one)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.PENDING)

        Attestation.objects.create(review=review, reviewer=reviewer_two)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.REVIEWED)

    def test_notify_reviewers_send_once(self):
        """Notification transports with send_once only notify a single reviewer."""
        obj = Group.objects.create(name=generate_id())
        rule = self._create_rule_for_object(obj)

        reviewer_one = create_test_user()
        reviewer_two = create_test_user()
        rule.reviewers.add(reviewer_one, reviewer_two)

        transport_once = NotificationTransport.objects.create(
            name=generate_id(),
            send_once=True,
        )
        transport_all = NotificationTransport.objects.create(
            name=generate_id(),
            send_once=False,
        )
        rule.notification_transports.add(transport_once, transport_all)

        event = Event.new(EventAction.REVIEW_INITIATED, target=obj)
        event.save()

        with patch(
            "authentik.enterprise.reviews.tasks.send_notification.send_with_options"
        ) as send_with_options:
            rule.notify_reviewers(event, NotificationSeverity.NOTICE)

            reviewer_pks = {reviewer_one.pk, reviewer_two.pk}
            self.assertEqual(send_with_options.call_count, len(reviewer_pks) + 1)

            calls = [call.kwargs["args"] for call in send_with_options.call_args_list]
            once_calls = [args for args in calls if args[0] == transport_once.pk]
            all_calls = [args for args in calls if args[0] == transport_all.pk]

            self.assertEqual(len(once_calls), 1)
            self.assertEqual(len(all_calls), len(reviewer_pks))
            self.assertIn(once_calls[0][2], reviewer_pks)
            self.assertEqual({args[2] for args in all_calls}, reviewer_pks)

    def test_apply_marks_overdue_and_opens_due_reviews(self):
        """Apply marks reviews overdue and opens new reviews when due."""
        app_one = Application.objects.create(name=generate_id(), slug=generate_id())
        app_two = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        rule_overdue = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_one.pk),
            interval_months=12,
            grace_period_days=10,
        )
        rule_new = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_two.pk),
            interval_months=1,
            grace_period_days=10,
        )

        review = Review.objects.create(content_type=content_type, object_id=str(app_one.pk))
        Review.objects.filter(pk=review.pk).update(
            opened_on=(timezone.now().date() - timedelta(days=20))
        )

        rule_overdue.apply()
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.OVERDUE)
        self.assertEqual(
            Review.objects.filter(content_type=content_type, object_id=str(app_one.pk)).count(),
            1,
        )

        rule_new.apply()
        self.assertEqual(
            Review.objects.filter(content_type=content_type, object_id=str(app_two.pk)).count(),
            1,
        )
        new_review = Review.objects.get(content_type=content_type, object_id=str(app_two.pk))
        self.assertEqual(new_review.state, ReviewState.PENDING)

    def test_apply_idempotent(self):
        """Apply is idempotent and does not create extra events or notifications."""
        app_due = Application.objects.create(name=generate_id(), slug=generate_id())
        app_overdue = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        rule_due = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_due.pk),
            interval_months=1,
            grace_period_days=30,
        )
        reviewer = create_test_user()
        rule_due.reviewers.add(reviewer)
        transport = NotificationTransport.objects.create(name=generate_id())
        rule_due.notification_transports.add(transport)

        rule_overdue = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_overdue.pk),
            interval_months=12,
            grace_period_days=10,
        )

        overdue_review = Review.objects.create(
            content_type=content_type,
            object_id=str(app_overdue.pk),
        )
        Review.objects.filter(pk=overdue_review.pk).update(
            opened_on=(timezone.now().date() - timedelta(days=20))
        )

        initiated_before = Event.objects.filter(action=EventAction.REVIEW_INITIATED).count()
        overdue_before = Event.objects.filter(action=EventAction.REVIEW_OVERDUE).count()

        with patch(
            "authentik.enterprise.reviews.tasks.send_notification.send_with_options"
        ) as send_with_options:
            rule_due.apply()
            rule_overdue.apply()

            due_review = Review.objects.get(content_type=content_type, object_id=str(app_due.pk))
            overdue_review.refresh_from_db()
            self.assertEqual(due_review.state, ReviewState.PENDING)
            self.assertEqual(overdue_review.state, ReviewState.OVERDUE)

            initiated_after_first = Event.objects.filter(
                action=EventAction.REVIEW_INITIATED
            ).count()
            overdue_after_first = Event.objects.filter(action=EventAction.REVIEW_OVERDUE).count()
            self.assertEqual(initiated_after_first, initiated_before + 1)
            self.assertEqual(overdue_after_first, overdue_before + 1)
            self.assertEqual(send_with_options.call_count, 1)

            rule_due.apply()
            rule_overdue.apply()

            due_review.refresh_from_db()
            overdue_review.refresh_from_db()
            self.assertEqual(due_review.state, ReviewState.PENDING)
            self.assertEqual(overdue_review.state, ReviewState.OVERDUE)
            self.assertEqual(
                Event.objects.filter(action=EventAction.REVIEW_INITIATED).count(),
                initiated_after_first,
            )
            self.assertEqual(
                Event.objects.filter(action=EventAction.REVIEW_OVERDUE).count(),
                overdue_after_first,
            )
            self.assertEqual(send_with_options.call_count, 1)
