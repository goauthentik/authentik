from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.enterprise.lifecycle.models import LifecycleIteration, LifecycleRule, ReviewState
from authentik.enterprise.reports.tests.utils import patch_license
from authentik.lib.generators import generate_id


@patch_license
class TestLifecycleRuleAPI(APITestCase):

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())
        self.content_type = ContentType.objects.get_for_model(Application)
        self.reviewer_group = Group.objects.create(name=generate_id())

    def test_list_rules(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(reverse("authentik_api:lifecyclerule-list"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_create_rule_with_reviewer_group(self):
        response = self.client.post(
            reverse("authentik_api:lifecyclerule-list"),
            {
                "name": generate_id(),
                "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                "object_id": str(self.app.pk),
                "interval": "days=30",
                "grace_period": "days=10",
                "reviewer_groups": [str(self.reviewer_group.pk)],
                "reviewers": [],
                "min_reviewers": 1,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["object_id"], str(self.app.pk))
        self.assertEqual(response.data["interval"], "days=30")

    def test_create_rule_with_explicit_reviewer(self):
        reviewer = create_test_user()
        response = self.client.post(
            reverse("authentik_api:lifecyclerule-list"),
            {
                "name": generate_id(),
                "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                "object_id": str(self.app.pk),
                "interval": "days=60",
                "grace_period": "days=15",
                "reviewer_groups": [],
                "reviewers": [str(reviewer.uuid)],
                "min_reviewers": 1,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn(reviewer.uuid, response.data["reviewers"])

    def test_create_rule_type_level(self):
        response = self.client.post(
            reverse("authentik_api:lifecyclerule-list"),
            {
                "name": generate_id(),
                "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                "object_id": None,
                "interval": "days=90",
                "grace_period": "days=30",
                "reviewer_groups": [str(self.reviewer_group.pk)],
                "reviewers": [],
                "min_reviewers": 1,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["object_id"])

    def test_create_rule_fails_without_reviewers(self):
        response = self.client.post(
            reverse("authentik_api:lifecyclerule-list"),
            {
                "name": generate_id(),
                "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                "object_id": str(self.app.pk),
                "interval": "days=30",
                "grace_period": "days=10",
                "reviewer_groups": [],
                "reviewers": [],
                "min_reviewers": 1,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_create_rule_fails_grace_period_longer_than_interval(self):
        response = self.client.post(
            reverse("authentik_api:lifecyclerule-list"),
            {
                "name": generate_id(),
                "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                "object_id": str(self.app.pk),
                "interval": "days=10",
                "grace_period": "days=30",
                "reviewer_groups": [str(self.reviewer_group.pk)],
                "reviewers": [],
                "min_reviewers": 1,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("grace_period", response.data)

    def test_create_rule_fails_invalid_object_id(self):
        response = self.client.post(
            reverse("authentik_api:lifecyclerule-list"),
            {
                "name": generate_id(),
                "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                "object_id": "00000000-0000-0000-0000-000000000000",
                "interval": "days=30",
                "grace_period": "days=10",
                "reviewer_groups": [str(self.reviewer_group.pk)],
                "reviewers": [],
                "min_reviewers": 1,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("object_id", response.data)

    def test_retrieve_rule(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(
            reverse("authentik_api:lifecyclerule-detail", kwargs={"pk": rule.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(rule.pk))

    def test_update_rule(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
            interval="days=30",
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.patch(
            reverse("authentik_api:lifecyclerule-detail", kwargs={"pk": rule.pk}),
            {"interval": "days=60"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["interval"], "days=60")

    def test_delete_rule(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.delete(
            reverse("authentik_api:lifecyclerule-detail", kwargs={"pk": rule.pk})
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(LifecycleRule.objects.filter(pk=rule.pk).exists())


@patch_license
class TestIterationAPI(APITestCase):

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())
        self.content_type = ContentType.objects.get_for_model(Application)
        self.reviewer_group = Group.objects.create(name=generate_id())
        self.reviewer_group.users.add(self.user)

    def test_open_iterations(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(reverse("authentik_api:lifecycleiteration-open-iterations"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)

        for iteration in response.data["results"]:
            self.assertEqual(iteration["state"], ReviewState.PENDING)

    def test_open_iterations_filter_user_is_reviewer(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(
            reverse("authentik_api:lifecycleiteration-open-iterations"),
            {"user_is_reviewer": "true"},
        )
        self.assertEqual(response.status_code, 200)
        # User is in reviewer_group, so should see the iteration
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_latest_iteration(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(
            reverse(
                "authentik_api:lifecycleiteration-latest-iteration",
                kwargs={
                    "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                    "object_id": str(self.app.pk),
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["object_id"], str(self.app.pk))

    def test_latest_iteration_not_found(self):
        response = self.client.get(
            reverse(
                "authentik_api:lifecycleiteration-latest-iteration",
                kwargs={
                    "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                    "object_id": "00000000-0000-0000-0000-000000000000",
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_iteration_includes_user_can_review(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(reverse("authentik_api:lifecycleiteration-open-iterations"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        # user_can_review should be present
        self.assertIn("user_can_review", response.data["results"][0])


@patch_license
class TestReviewAPI(APITestCase):

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())
        self.content_type = ContentType.objects.get_for_model(Application)
        self.reviewer_group = Group.objects.create(name=generate_id())
        self.reviewer_group.users.add(self.user)

    def test_create_review(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(self.reviewer_group)

        # Get the auto-created iteration
        iteration = LifecycleIteration.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        response = self.client.post(
            reverse("authentik_api:review-list"),
            {
                "iteration": str(iteration.pk),
                "note": "Reviewed and approved",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["iteration"], iteration.pk)
        self.assertEqual(response.data["note"], "Reviewed and approved")
        self.assertEqual(response.data["reviewer"]["pk"], self.user.pk)

    def test_create_review_completes_iteration(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(self.reviewer_group)

        iteration = LifecycleIteration.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )
        self.assertEqual(iteration.state, ReviewState.PENDING)

        response = self.client.post(
            reverse("authentik_api:review-list"),
            {
                "iteration": str(iteration.pk),
            },
        )
        self.assertEqual(response.status_code, 201)

        iteration.refresh_from_db()
        self.assertEqual(iteration.state, ReviewState.REVIEWED)

    def test_create_review_sets_reviewer_from_request(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(self.reviewer_group)

        iteration = LifecycleIteration.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        response = self.client.post(
            reverse("authentik_api:review-list"),
            {
                "iteration": str(iteration.pk),
            },
        )
        self.assertEqual(response.status_code, 201)
        # Reviewer should be the logged-in user
        self.assertEqual(response.data["reviewer"]["pk"], self.user.pk)

    def test_non_reviewer_cannot_review(self):
        other_group = Group.objects.create(name=generate_id())
        other_user = create_test_user()
        other_group.users.add(other_user)

        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(other_group)

        iteration = LifecycleIteration.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        # Current user is not in the reviewer group
        self.assertFalse(iteration.user_can_review(self.user))

    def test_non_reviewer_review_via_api_rejected(self):
        other_group = Group.objects.create(name=generate_id())
        other_user = create_test_user()
        other_group.users.add(other_user)

        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(other_group)

        iteration = LifecycleIteration.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        # Current user (self.user) is NOT in the reviewer group
        response = self.client.post(
            reverse("authentik_api:review-list"),
            {"iteration": str(iteration.pk)},
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_review_via_api_rejected(self):
        rule = LifecycleRule.objects.create(
            name=generate_id(),
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=2,
        )
        rule.reviewer_groups.add(self.reviewer_group)

        iteration = LifecycleIteration.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        # First review should succeed
        response = self.client.post(
            reverse("authentik_api:review-list"),
            {"iteration": str(iteration.pk)},
        )
        self.assertEqual(response.status_code, 201)

        # Second review by same user should be rejected
        response = self.client.post(
            reverse("authentik_api:review-list"),
            {"iteration": str(iteration.pk)},
        )
        self.assertEqual(response.status_code, 400)
