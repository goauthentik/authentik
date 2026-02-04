from datetime import timedelta
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.utils import timezone

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.lifecycle.models import Attestation, LifecycleRule, Review, ReviewState
from authentik.events.models import (
    Event,
    EventAction,
    NotificationSeverity,
    NotificationTransport,
)
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


class TestLifecycleModels(TestCase):
    """Tests for access review models."""

    def setUp(self):
        self.factory = RequestFactory()

    def _get_request(self):
        return self.factory.get("/")

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

    def _create_rule_for_type(self, model, **kwargs) -> LifecycleRule:
        content_type = ContentType.objects.get_for_model(model)
        return LifecycleRule.objects.create(
            content_type=content_type,
            object_id=None,
            **kwargs,
        )

    def test_review_start_supported_objects(self):
        """Ensure reviews are automatically started for applications, roles, and groups."""
        for model in (Application, Role, Group):
            with self.subTest(model=model.__name__):
                obj = self._create_object(model)
                content_type = ContentType.objects.get_for_model(obj)

                before_events = Event.objects.filter(action=EventAction.REVIEW_INITIATED).count()
                # Creating a rule automatically triggers apply() which creates a review
                rule = self._create_rule_for_object(obj)

                # Verify review was created automatically
                review = Review.objects.get(
                    content_type=content_type, object_id=str(obj.pk), rule=rule
                )
                self.assertEqual(review.state, ReviewState.PENDING)
                self.assertEqual(review.object, obj)
                self.assertEqual(review.rule, rule)
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
        # Review is created automatically when rule is saved
        review = Review.objects.get(content_type=content_type, object_id=str(obj.pk), rule=rule)
        request = self._get_request()

        Attestation.objects.create(review=review, reviewer=reviewer_one)
        review.on_attestation(request)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.PENDING)

        Attestation.objects.create(review=review, reviewer=reviewer_two)
        review.on_attestation(request)
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
        # Review is created automatically when rule is saved
        review = Review.objects.get(content_type=content_type, object_id=str(obj.pk), rule=rule)
        request = self._get_request()

        Attestation.objects.create(review=review, reviewer=reviewer_one)
        review.on_attestation(request)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.PENDING)

        Attestation.objects.create(review=review, reviewer=reviewer_two)
        review.on_attestation(request)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.REVIEWED)

    def test_attestation_explicit_and_group_reviewers(self):
        """Reviews require both explicit reviewers AND min_reviewers from groups."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj, min_reviewers=1)

        reviewer_group = Group.objects.create(name=generate_id())
        group_member = create_test_user()
        reviewer_group.users.add(group_member)
        rule.reviewer_groups.add(reviewer_group)

        explicit_reviewer = create_test_user()
        rule.reviewers.add(explicit_reviewer)

        content_type = ContentType.objects.get_for_model(obj)
        # Review is created automatically when rule is saved
        review = Review.objects.get(content_type=content_type, object_id=str(obj.pk), rule=rule)
        request = self._get_request()

        # Only group member attests - not satisfied (explicit reviewer missing)
        Attestation.objects.create(review=review, reviewer=group_member)
        review.on_attestation(request)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.PENDING)

        # Explicit reviewer attests - now satisfied
        Attestation.objects.create(review=review, reviewer=explicit_reviewer)
        review.on_attestation(request)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.REVIEWED)

    def test_attestation_min_reviewers_per_group(self):
        """With min_reviewers_is_per_group=True, each group needs min_reviewers attestations."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj, min_reviewers=1, min_reviewers_is_per_group=True)

        group_one = Group.objects.create(name=generate_id())
        group_two = Group.objects.create(name=generate_id())
        member_group_one = create_test_user()
        member_group_two = create_test_user()
        group_one.users.add(member_group_one)
        group_two.users.add(member_group_two)
        rule.reviewer_groups.add(group_one, group_two)

        content_type = ContentType.objects.get_for_model(obj)
        # Review is created automatically when rule is saved
        review = Review.objects.get(content_type=content_type, object_id=str(obj.pk), rule=rule)
        request = self._get_request()

        # Only member from group_one attests - not satisfied (need member from each group)
        Attestation.objects.create(review=review, reviewer=member_group_one)
        review.on_attestation(request)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.PENDING)

        # Member from group_two attests - now satisfied
        Attestation.objects.create(review=review, reviewer=member_group_two)
        review.on_attestation(request)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.REVIEWED)

    def test_attestation_reviewers_from_child_groups(self):
        """Reviewers from child groups can satisfy attestation requirements."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj, min_reviewers=1)

        parent_group = Group.objects.create(name=generate_id())
        child_group = Group.objects.create(name=generate_id())
        child_group.parents.add(parent_group)

        child_member = create_test_user()
        child_group.users.add(child_member)

        rule.reviewer_groups.add(parent_group)

        content_type = ContentType.objects.get_for_model(obj)
        # Review is created automatically when rule is saved
        review = Review.objects.get(content_type=content_type, object_id=str(obj.pk), rule=rule)
        request = self._get_request()

        # Child group member should be able to attest
        self.assertTrue(review.user_can_attest(child_member))

        Attestation.objects.create(review=review, reviewer=child_member)
        review.on_attestation(request)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.REVIEWED)

    def test_attestation_reviewers_from_nested_child_groups(self):
        """Reviewers from deeply nested child groups can satisfy attestation requirements."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj, min_reviewers=2)

        grandparent = Group.objects.create(name=generate_id())
        parent = Group.objects.create(name=generate_id())
        child = Group.objects.create(name=generate_id())
        parent.parents.add(grandparent)
        child.parents.add(parent)

        parent_member = create_test_user()
        child_member = create_test_user()
        parent.users.add(parent_member)
        child.users.add(child_member)

        rule.reviewer_groups.add(grandparent)

        content_type = ContentType.objects.get_for_model(obj)
        # Review is created automatically when rule is saved
        review = Review.objects.get(content_type=content_type, object_id=str(obj.pk), rule=rule)
        request = self._get_request()

        # Both nested members should be able to attest
        self.assertTrue(review.user_can_attest(parent_member))
        self.assertTrue(review.user_can_attest(child_member))

        Attestation.objects.create(review=review, reviewer=parent_member)
        review.on_attestation(request)
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.PENDING)

        Attestation.objects.create(review=review, reviewer=child_member)
        review.on_attestation(request)
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
            "authentik.enterprise.lifecycle.tasks.send_notification.send_with_options"
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

        # Creating rule triggers apply() automatically, creating a review
        rule_overdue = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_one.pk),
            interval="days=365",
            grace_period="days=10",
        )

        # Get the automatically created review and backdate it past the grace period
        review = Review.objects.get(
            content_type=content_type, object_id=str(app_one.pk), rule=rule_overdue
        )
        Review.objects.filter(pk=review.pk).update(
            opened_on=(timezone.now().date() - timedelta(days=20))
        )

        # Apply again to trigger overdue logic
        rule_overdue.apply()
        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.OVERDUE)
        self.assertEqual(
            Review.objects.filter(content_type=content_type, object_id=str(app_one.pk)).count(),
            1,
        )

        # Creating rule_new triggers apply() automatically, creating a review for app_two
        rule_new = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_two.pk),
            interval="days=30",
            grace_period="days=10",
        )
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

        initiated_before = Event.objects.filter(action=EventAction.REVIEW_INITIATED).count()
        overdue_before = Event.objects.filter(action=EventAction.REVIEW_OVERDUE).count()

        rule_due = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_due.pk),
            interval="days=30",
            grace_period="days=30",
        )
        reviewer = create_test_user()
        rule_due.reviewers.add(reviewer)
        transport = NotificationTransport.objects.create(name=generate_id())
        rule_due.notification_transports.add(transport)

        # Creating rule triggers automatic apply() which creates a review
        rule_overdue = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_overdue.pk),
            interval="days=365",
            grace_period="days=10",
        )

        # Get the automatically created review for overdue app and backdate it
        overdue_review = Review.objects.get(
            content_type=content_type, object_id=str(app_overdue.pk), rule=rule_overdue
        )
        Review.objects.filter(pk=overdue_review.pk).update(
            opened_on=(timezone.now().date() - timedelta(days=20))
        )

        # Apply overdue rule to mark review as overdue
        rule_overdue.apply()

        due_review = Review.objects.get(content_type=content_type, object_id=str(app_due.pk))
        overdue_review.refresh_from_db()
        self.assertEqual(due_review.state, ReviewState.PENDING)
        self.assertEqual(overdue_review.state, ReviewState.OVERDUE)

        initiated_after_first = Event.objects.filter(
            action=EventAction.REVIEW_INITIATED
        ).count()
        overdue_after_first = Event.objects.filter(action=EventAction.REVIEW_OVERDUE).count()
        # Both rules created reviews on save
        self.assertEqual(initiated_after_first, initiated_before + 2)
        self.assertEqual(overdue_after_first, overdue_before + 1)

        # Apply again - should be idempotent
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

    def test_rule_matches_entire_type(self):
        """A rule with object_id=None matches all objects of that type."""
        app_one = Application.objects.create(name=generate_id(), slug=generate_id())
        app_two = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        rule = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=None,
            interval="days=30",
            grace_period="days=10",
        )

        objects = list(rule.get_objects())
        self.assertIn(app_one, objects)
        self.assertIn(app_two, objects)

    def test_rule_type_excludes_objects_with_specific_rules(self):
        """A type-level rule excludes objects that have their own specific rules."""
        app_with_rule = Application.objects.create(name=generate_id(), slug=generate_id())
        app_without_rule = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        # Create a specific rule for app_with_rule
        LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_with_rule.pk),
            interval="days=30",
        )

        # Create a type-level rule
        type_rule = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=None,
            interval="days=60",
        )

        objects = list(type_rule.get_objects())
        self.assertNotIn(app_with_rule, objects)
        self.assertIn(app_without_rule, objects)

    def test_rule_type_apply_creates_reviews_for_all_objects(self):
        """Creating a type-level rule automatically creates reviews for all matching objects."""
        # Clean up any existing applications to have a controlled test
        Application.objects.all().delete()

        app_one = Application.objects.create(name=generate_id(), slug=generate_id())
        app_two = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        # Creating rule triggers automatic apply() which creates reviews for all matching objects
        LifecycleRule.objects.create(
            content_type=content_type,
            object_id=None,
            interval="days=30",
            grace_period="days=10",
        )

        self.assertTrue(
            Review.objects.filter(content_type=content_type, object_id=str(app_one.pk)).exists()
        )
        self.assertTrue(
            Review.objects.filter(content_type=content_type, object_id=str(app_two.pk)).exists()
        )

    def test_delete_rule_cancels_open_reviews(self):
        """Deleting a rule cancels all pending and overdue reviews for that rule."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        # Creating rule triggers automatic apply() which creates a PENDING review
        rule = self._create_rule_for_object(obj)
        content_type = ContentType.objects.get_for_model(obj)

        # Get the automatically created pending review
        pending_review = Review.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )
        self.assertEqual(pending_review.state, ReviewState.PENDING)

        # Create additional reviews in other states for testing
        overdue_review = Review.objects.create(
            content_type=content_type,
            object_id=str(obj.pk),
            rule=rule,
            state=ReviewState.OVERDUE,
        )
        reviewed_review = Review.objects.create(
            content_type=content_type,
            object_id=str(obj.pk),
            rule=rule,
            state=ReviewState.REVIEWED,
        )

        rule.delete()

        pending_review.refresh_from_db()
        overdue_review.refresh_from_db()
        reviewed_review.refresh_from_db()

        self.assertEqual(pending_review.state, ReviewState.CANCELED)
        self.assertEqual(overdue_review.state, ReviewState.CANCELED)
        self.assertEqual(reviewed_review.state, ReviewState.REVIEWED)  # Not affected

    def test_update_rule_target_cancels_stale_reviews(self):
        """Changing a rule's target object cancels reviews for the old object."""
        app_one = Application.objects.create(name=generate_id(), slug=generate_id())
        app_two = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        # Creating rule triggers automatic apply() which creates a review for app_one
        rule = LifecycleRule.objects.create(
            content_type=content_type,
            object_id=str(app_one.pk),
            interval="days=30",
        )

        # Get the automatically created review
        review_for_app_one = Review.objects.get(
            content_type=content_type, object_id=str(app_one.pk), rule=rule
        )
        self.assertEqual(review_for_app_one.state, ReviewState.PENDING)

        # Change rule target to app_two - save() triggers apply() which cancels stale reviews
        rule.object_id = str(app_two.pk)
        rule.save()

        review_for_app_one.refresh_from_db()
        self.assertEqual(review_for_app_one.state, ReviewState.CANCELED)

    def test_update_rule_content_type_cancels_stale_reviews(self):
        """Changing a rule's content type cancels reviews for the old type."""
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        group = Group.objects.create(name=generate_id())
        app_content_type = ContentType.objects.get_for_model(Application)
        group_content_type = ContentType.objects.get_for_model(Group)

        # Creating rule triggers automatic apply() which creates a review for app
        rule = LifecycleRule.objects.create(
            content_type=app_content_type,
            object_id=str(app.pk),
            interval="days=30",
        )

        # Get the automatically created review
        review = Review.objects.get(
            content_type=app_content_type, object_id=str(app.pk), rule=rule
        )
        self.assertEqual(review.state, ReviewState.PENDING)

        # Change content type to Group - save() triggers apply() which cancels stale reviews
        rule.content_type = group_content_type
        rule.object_id = str(group.pk)
        rule.save()

        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.CANCELED)

    def test_user_can_attest_checks_group_hierarchy(self):
        """user_can_attest respects group hierarchy for reviewer groups."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj)

        parent_group = Group.objects.create(name=generate_id())
        child_group = Group.objects.create(name=generate_id())
        child_group.parents.add(parent_group)

        parent_member = create_test_user()
        child_member = create_test_user()
        non_member = create_test_user()
        parent_group.users.add(parent_member)
        child_group.users.add(child_member)

        rule.reviewer_groups.add(parent_group)

        content_type = ContentType.objects.get_for_model(obj)
        # Review is created automatically when rule is saved
        review = Review.objects.get(content_type=content_type, object_id=str(obj.pk), rule=rule)

        self.assertTrue(review.user_can_attest(parent_member))
        self.assertTrue(review.user_can_attest(child_member))
        self.assertFalse(review.user_can_attest(non_member))

    def test_user_cannot_attest_twice(self):
        """A user cannot attest to the same review twice."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj)
        reviewer = create_test_user()
        rule.reviewers.add(reviewer)

        content_type = ContentType.objects.get_for_model(obj)
        # Review is created automatically when rule is saved
        review = Review.objects.get(content_type=content_type, object_id=str(obj.pk), rule=rule)

        self.assertTrue(review.user_can_attest(reviewer))

        Attestation.objects.create(review=review, reviewer=reviewer)

        self.assertFalse(review.user_can_attest(reviewer))

    def test_user_cannot_attest_completed_review(self):
        """Users cannot attest to reviews that are already completed or canceled."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj)
        reviewer = create_test_user()
        rule.reviewers.add(reviewer)

        content_type = ContentType.objects.get_for_model(obj)

        # Get the automatically created pending review and test with different states
        review = Review.objects.get(content_type=content_type, object_id=str(obj.pk), rule=rule)

        for state in (ReviewState.REVIEWED, ReviewState.CANCELED):
            review.state = state
            review.save()
            self.assertFalse(review.user_can_attest(reviewer))

    def test_get_reviewers_includes_child_group_members(self):
        """get_reviewers includes members of child groups."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj)

        parent_group = Group.objects.create(name=generate_id())
        child_group = Group.objects.create(name=generate_id())
        child_group.parents.add(parent_group)

        parent_member = create_test_user()
        child_member = create_test_user()
        parent_group.users.add(parent_member)
        child_group.users.add(child_member)

        rule.reviewer_groups.add(parent_group)

        reviewers = list(rule.get_reviewers())
        self.assertIn(parent_member, reviewers)
        self.assertIn(child_member, reviewers)

    def test_get_reviewers_includes_explicit_reviewers(self):
        """get_reviewers includes both explicit reviewers and group members."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj)

        explicit_reviewer = create_test_user()
        rule.reviewers.add(explicit_reviewer)

        group = Group.objects.create(name=generate_id())
        group_member = create_test_user()
        group.users.add(group_member)
        rule.reviewer_groups.add(group)

        reviewers = list(rule.get_reviewers())
        self.assertIn(explicit_reviewer, reviewers)
        self.assertIn(group_member, reviewers)
