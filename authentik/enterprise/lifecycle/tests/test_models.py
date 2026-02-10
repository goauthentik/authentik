from datetime import timedelta
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.utils import timezone

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.lifecycle.models import (
    LifecycleIteration,
    LifecycleRule,
    Review,
    ReviewState,
)
from authentik.events.models import (
    Event,
    EventAction,
    NotificationSeverity,
    NotificationTransport,
)
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


class TestLifecycleModels(TestCase):

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
            name=generate_id(),
            content_type=content_type,
            object_id=str(obj.pk),
            **kwargs,
        )

    def _create_rule_for_type(self, model, **kwargs) -> LifecycleRule:
        content_type = ContentType.objects.get_for_model(model)
        return LifecycleRule.objects.create(
            name=generate_id(),
            content_type=content_type,
            object_id=None,
            **kwargs,
        )

    def test_iteration_start_supported_objects(self):
        """Ensure iterations are automatically started for applications, roles, and groups."""
        for model in (Application, Role, Group):
            with self.subTest(model=model.__name__):
                obj = self._create_object(model)
                content_type = ContentType.objects.get_for_model(obj)

                before_events = Event.objects.filter(action=EventAction.REVIEW_INITIATED).count()

                rule = self._create_rule_for_object(obj)

                # Verify iteration was created automatically
                iteration = LifecycleIteration.objects.get(
                    content_type=content_type, object_id=str(obj.pk), rule=rule
                )
                self.assertEqual(iteration.state, ReviewState.PENDING)
                self.assertEqual(iteration.object, obj)
                self.assertEqual(iteration.rule, rule)
                self.assertEqual(
                    Event.objects.filter(action=EventAction.REVIEW_INITIATED).count(),
                    before_events + 1,
                )

    def test_review_requires_all_explicit_reviewers(self):
        obj = Group.objects.create(name=generate_id())
        rule = self._create_rule_for_object(obj)
        reviewer_one = create_test_user()
        reviewer_two = create_test_user()
        rule.reviewers.add(reviewer_one, reviewer_two)

        content_type = ContentType.objects.get_for_model(obj)

        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )
        request = self._get_request()

        Review.objects.create(iteration=iteration, reviewer=reviewer_one)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.PENDING)

        Review.objects.create(iteration=iteration, reviewer=reviewer_two)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.REVIEWED)
        self.assertTrue(Event.objects.filter(action=EventAction.REVIEW_COMPLETED).exists())

    def test_review_min_reviewers_from_groups(self):
        """Group-based reviews complete once the minimum number of reviewers review."""
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj, min_reviewers=2)

        reviewer_group = Group.objects.create(name=generate_id())
        reviewer_one = create_test_user()
        reviewer_two = create_test_user()
        reviewer_group.users.add(reviewer_one, reviewer_two)
        rule.reviewer_groups.add(reviewer_group)

        content_type = ContentType.objects.get_for_model(obj)

        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )
        request = self._get_request()

        Review.objects.create(iteration=iteration, reviewer=reviewer_one)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.PENDING)

        Review.objects.create(iteration=iteration, reviewer=reviewer_two)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.REVIEWED)

    def test_review_explicit_and_group_reviewers(self):
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

        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )
        request = self._get_request()

        # Only group member reviews - not satisfied (explicit reviewer missing)
        Review.objects.create(iteration=iteration, reviewer=group_member)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.PENDING)

        # Explicit reviewer reviews - now satisfied
        Review.objects.create(iteration=iteration, reviewer=explicit_reviewer)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.REVIEWED)

    def test_review_min_reviewers_per_group(self):
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

        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )
        request = self._get_request()

        # Only member from group_one reviews - not satisfied (need member from each group)
        Review.objects.create(iteration=iteration, reviewer=member_group_one)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.PENDING)

        # Member from group_two reviews - now satisfied
        Review.objects.create(iteration=iteration, reviewer=member_group_two)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.REVIEWED)

    def test_review_reviewers_from_child_groups(self):
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj, min_reviewers=1)

        parent_group = Group.objects.create(name=generate_id())
        child_group = Group.objects.create(name=generate_id())
        child_group.parents.add(parent_group)

        child_member = create_test_user()
        child_group.users.add(child_member)

        rule.reviewer_groups.add(parent_group)

        content_type = ContentType.objects.get_for_model(obj)

        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )
        request = self._get_request()

        # Child group member should be able to review
        self.assertTrue(iteration.user_can_review(child_member))

        Review.objects.create(iteration=iteration, reviewer=child_member)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.REVIEWED)

    def test_review_reviewers_from_nested_child_groups(self):
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

        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )
        request = self._get_request()

        # Both nested members should be able to review
        self.assertTrue(iteration.user_can_review(parent_member))
        self.assertTrue(iteration.user_can_review(child_member))

        Review.objects.create(iteration=iteration, reviewer=parent_member)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.PENDING)

        Review.objects.create(iteration=iteration, reviewer=child_member)
        iteration.on_review(request)
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.REVIEWED)

    def test_notify_reviewers_send_once(self):
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
        app_one = Application.objects.create(name=generate_id(), slug=generate_id())
        app_two = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        rule_overdue = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=content_type,
            object_id=str(app_one.pk),
            interval="days=365",
            grace_period="days=10",
        )

        # Get the automatically created iteration and backdate it past the grace period
        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(app_one.pk), rule=rule_overdue
        )
        LifecycleIteration.objects.filter(pk=iteration.pk).update(
            opened_on=(timezone.now().date() - timedelta(days=20))
        )

        # Apply again to trigger overdue logic
        rule_overdue.apply()
        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.OVERDUE)
        self.assertEqual(
            LifecycleIteration.objects.filter(
                content_type=content_type, object_id=str(app_one.pk)
            ).count(),
            1,
        )

        LifecycleRule.objects.create(
            name=generate_id(),
            content_type=content_type,
            object_id=str(app_two.pk),
            interval="days=30",
            grace_period="days=10",
        )
        self.assertEqual(
            LifecycleIteration.objects.filter(
                content_type=content_type, object_id=str(app_two.pk)
            ).count(),
            1,
        )
        new_iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(app_two.pk)
        )
        self.assertEqual(new_iteration.state, ReviewState.PENDING)

    def test_apply_idempotent(self):
        app_due = Application.objects.create(name=generate_id(), slug=generate_id())
        app_overdue = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        initiated_before = Event.objects.filter(action=EventAction.REVIEW_INITIATED).count()
        overdue_before = Event.objects.filter(action=EventAction.REVIEW_OVERDUE).count()

        rule_due = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=content_type,
            object_id=str(app_due.pk),
            interval="days=30",
            grace_period="days=30",
        )
        reviewer = create_test_user()
        rule_due.reviewers.add(reviewer)
        transport = NotificationTransport.objects.create(name=generate_id())
        rule_due.notification_transports.add(transport)

        rule_overdue = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=content_type,
            object_id=str(app_overdue.pk),
            interval="days=365",
            grace_period="days=10",
        )

        overdue_iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(app_overdue.pk), rule=rule_overdue
        )
        LifecycleIteration.objects.filter(pk=overdue_iteration.pk).update(
            opened_on=(timezone.now().date() - timedelta(days=20))
        )

        # Apply overdue rule to mark iteration as overdue
        rule_overdue.apply()

        due_iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(app_due.pk)
        )
        overdue_iteration.refresh_from_db()
        self.assertEqual(due_iteration.state, ReviewState.PENDING)
        self.assertEqual(overdue_iteration.state, ReviewState.OVERDUE)

        initiated_after_first = Event.objects.filter(action=EventAction.REVIEW_INITIATED).count()
        overdue_after_first = Event.objects.filter(action=EventAction.REVIEW_OVERDUE).count()
        # Both rules created iterations on save
        self.assertEqual(initiated_after_first, initiated_before + 2)
        self.assertEqual(overdue_after_first, overdue_before + 1)

        # Apply again - should be idempotent
        rule_due.apply()
        rule_overdue.apply()

        due_iteration.refresh_from_db()
        overdue_iteration.refresh_from_db()
        self.assertEqual(due_iteration.state, ReviewState.PENDING)
        self.assertEqual(overdue_iteration.state, ReviewState.OVERDUE)
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
            name=generate_id(),
            content_type=content_type,
            object_id=None,
            interval="days=30",
            grace_period="days=10",
        )

        objects = list(rule.get_objects())
        self.assertIn(app_one, objects)
        self.assertIn(app_two, objects)

    def test_rule_type_excludes_objects_with_specific_rules(self):
        app_with_rule = Application.objects.create(name=generate_id(), slug=generate_id())
        app_without_rule = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        # Create a specific rule for app_with_rule
        LifecycleRule.objects.create(
            name=generate_id(),
            content_type=content_type,
            object_id=str(app_with_rule.pk),
            interval="days=30",
        )

        # Create a type-level rule
        type_rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=content_type,
            object_id=None,
            interval="days=60",
        )

        objects = list(type_rule.get_objects())
        self.assertNotIn(app_with_rule, objects)
        self.assertIn(app_without_rule, objects)

    def test_rule_type_apply_creates_iterations_for_all_objects(self):
        app_one = Application.objects.create(name=generate_id(), slug=generate_id())
        app_two = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        LifecycleRule.objects.create(
            name=generate_id(),
            content_type=content_type,
            object_id=None,
            interval="days=30",
            grace_period="days=10",
        )

        self.assertTrue(
            LifecycleIteration.objects.filter(
                content_type=content_type, object_id=str(app_one.pk)
            ).exists()
        )
        self.assertTrue(
            LifecycleIteration.objects.filter(
                content_type=content_type, object_id=str(app_two.pk)
            ).exists()
        )

    def test_delete_rule_cancels_open_iterations(self):
        obj = Application.objects.create(name=generate_id(), slug=generate_id())

        rule = self._create_rule_for_object(obj)
        content_type = ContentType.objects.get_for_model(obj)

        pending_iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )
        self.assertEqual(pending_iteration.state, ReviewState.PENDING)

        overdue_iteration = LifecycleIteration.objects.create(
            content_type=content_type,
            object_id=str(obj.pk),
            rule=rule,
            state=ReviewState.OVERDUE,
        )
        reviewed_iteration = LifecycleIteration.objects.create(
            content_type=content_type,
            object_id=str(obj.pk),
            rule=rule,
            state=ReviewState.REVIEWED,
        )

        rule.delete()

        pending_iteration.refresh_from_db()
        overdue_iteration.refresh_from_db()
        reviewed_iteration.refresh_from_db()

        self.assertEqual(pending_iteration.state, ReviewState.CANCELED)
        self.assertEqual(overdue_iteration.state, ReviewState.CANCELED)
        self.assertEqual(reviewed_iteration.state, ReviewState.REVIEWED)  # Not affected

    def test_update_rule_target_cancels_stale_iterations(self):
        app_one = Application.objects.create(name=generate_id(), slug=generate_id())
        app_two = Application.objects.create(name=generate_id(), slug=generate_id())
        content_type = ContentType.objects.get_for_model(Application)

        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=content_type,
            object_id=str(app_one.pk),
            interval="days=30",
        )

        iteration_for_app_one = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(app_one.pk), rule=rule
        )
        self.assertEqual(iteration_for_app_one.state, ReviewState.PENDING)

        # Change rule target to app_two - save() triggers apply() which cancels stale iterations
        rule.object_id = str(app_two.pk)
        rule.save()

        iteration_for_app_one.refresh_from_db()
        self.assertEqual(iteration_for_app_one.state, ReviewState.CANCELED)

    def test_update_rule_content_type_cancels_stale_iterations(self):
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        group = Group.objects.create(name=generate_id())
        app_content_type = ContentType.objects.get_for_model(Application)
        group_content_type = ContentType.objects.get_for_model(Group)

        # Creating rule triggers automatic apply() which creates a iteration for app
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=app_content_type,
            object_id=str(app.pk),
            interval="days=30",
        )

        iteration = LifecycleIteration.objects.get(
            content_type=app_content_type, object_id=str(app.pk), rule=rule
        )
        self.assertEqual(iteration.state, ReviewState.PENDING)

        # Change content type to Group - save() triggers apply() which cancels stale iterations
        rule.content_type = group_content_type
        rule.object_id = str(group.pk)
        rule.save()

        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.CANCELED)

    def test_user_can_review_checks_group_hierarchy(self):
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
        # iteration is created automatically when rule is saved
        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )

        self.assertTrue(iteration.user_can_review(parent_member))
        self.assertTrue(iteration.user_can_review(child_member))
        self.assertFalse(iteration.user_can_review(non_member))

    def test_user_cannot_review_twice(self):
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj)
        reviewer = create_test_user()
        rule.reviewers.add(reviewer)

        content_type = ContentType.objects.get_for_model(obj)
        # iteration is created automatically when rule is saved
        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )

        self.assertTrue(iteration.user_can_review(reviewer))

        Review.objects.create(iteration=iteration, reviewer=reviewer)

        self.assertFalse(iteration.user_can_review(reviewer))

    def test_user_cannot_review_completed_iteration(self):
        obj = Application.objects.create(name=generate_id(), slug=generate_id())
        rule = self._create_rule_for_object(obj)
        reviewer = create_test_user()
        rule.reviewers.add(reviewer)

        content_type = ContentType.objects.get_for_model(obj)

        # Get the automatically created pending iteration and test with different states
        iteration = LifecycleIteration.objects.get(
            content_type=content_type, object_id=str(obj.pk), rule=rule
        )

        for state in (ReviewState.REVIEWED, ReviewState.CANCELED):
            iteration.state = state
            iteration.save()
            self.assertFalse(iteration.user_can_review(reviewer))

    def test_get_reviewers_includes_child_group_members(self):
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
