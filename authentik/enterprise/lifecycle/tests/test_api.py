from unittest.mock import MagicMock, patch

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.enterprise.lifecycle.models import LifecycleRule, Review, ReviewState
from authentik.lib.generators import generate_id
from authentik.enterprise.reports.tests.utils import patch_license



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
class TestReviewAPI(APITestCase):

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())
        self.content_type = ContentType.objects.get_for_model(Application)
        self.reviewer_group = Group.objects.create(name=generate_id())
        self.reviewer_group.users.add(self.user)

    def test_open_reviews(self):
        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(reverse("authentik_api:review-open-reviews"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)

        for review in response.data["results"]:
            self.assertEqual(review["state"], ReviewState.PENDING)

    def test_open_reviews_filter_user_is_reviewer(self):
        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(
            reverse("authentik_api:review-open-reviews"), {"user_is_reviewer": "true"}
        )
        self.assertEqual(response.status_code, 200)
        # User is in reviewer_group, so should see the review
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_latest_review(self):
        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(
            reverse(
                "authentik_api:review-latest-review",
                kwargs={
                    "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                    "object_id": str(self.app.pk),
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["object_id"], str(self.app.pk))

    def test_latest_review_not_found(self):
        response = self.client.get(
            reverse(
                "authentik_api:review-latest-review",
                kwargs={
                    "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
                    "object_id": "00000000-0000-0000-0000-000000000000",
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_review_includes_user_can_attest(self):
        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
        )
        rule.reviewer_groups.add(self.reviewer_group)

        response = self.client.get(reverse("authentik_api:review-open-reviews"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        # user_can_attest should be present
        self.assertIn("user_can_attest", response.data["results"][0])


@patch_license
class TestAttestationAPI(APITestCase):

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())
        self.content_type = ContentType.objects.get_for_model(Application)
        self.reviewer_group = Group.objects.create(name=generate_id())
        self.reviewer_group.users.add(self.user)

    def test_create_attestation(self):
        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(self.reviewer_group)

        # Get the auto-created review
        review = Review.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        response = self.client.post(
            reverse("authentik_api:attestation-list"),
            {
                "review": str(review.pk),
                "note": "Reviewed and approved",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["review"], review.pk)
        self.assertEqual(response.data["note"], "Reviewed and approved")
        self.assertEqual(response.data["reviewer"]["pk"], self.user.pk)

    def test_create_attestation_completes_review(self):
        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(self.reviewer_group)

        review = Review.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )
        self.assertEqual(review.state, ReviewState.PENDING)

        response = self.client.post(
            reverse("authentik_api:attestation-list"),
            {
                "review": str(review.pk),
            },
        )
        self.assertEqual(response.status_code, 201)

        review.refresh_from_db()
        self.assertEqual(review.state, ReviewState.REVIEWED)

    def test_create_attestation_sets_reviewer_from_request(self):
        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(self.reviewer_group)

        review = Review.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        response = self.client.post(
            reverse("authentik_api:attestation-list"),
            {
                "review": str(review.pk),
            },
        )
        self.assertEqual(response.status_code, 201)
        # Reviewer should be the logged-in user
        self.assertEqual(response.data["reviewer"]["pk"], self.user.pk)

    def test_non_reviewer_cannot_attest(self):
        other_group = Group.objects.create(name=generate_id())
        other_user = create_test_user()
        other_group.users.add(other_user)

        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(other_group)

        review = Review.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        # Current user is not in the reviewer group
        self.assertFalse(review.user_can_attest(self.user))

    def test_non_reviewer_attestation_via_api_rejected(self):
        other_group = Group.objects.create(name=generate_id())
        other_user = create_test_user()
        other_group.users.add(other_user)

        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=1,
        )
        rule.reviewer_groups.add(other_group)

        review = Review.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        # Current user (self.user) is NOT in the reviewer group
        response = self.client.post(
            reverse("authentik_api:attestation-list"),
            {"review": str(review.pk)},
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_attestation_via_api_rejected(self):
        rule = LifecycleRule.objects.create(
            content_type=self.content_type,
            object_id=str(self.app.pk),
            min_reviewers=2,
        )
        rule.reviewer_groups.add(self.reviewer_group)

        review = Review.objects.get(
            content_type=self.content_type, object_id=str(self.app.pk), rule=rule
        )

        # First attestation should succeed
        response = self.client.post(
            reverse("authentik_api:attestation-list"),
            {"review": str(review.pk)},
        )
        self.assertEqual(response.status_code, 201)

        # Second attestation by same user should be rejected
        response = self.client.post(
            reverse("authentik_api:attestation-list"),
            {"review": str(review.pk)},
        )
        self.assertEqual(response.status_code, 400)

