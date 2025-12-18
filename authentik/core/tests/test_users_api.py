"""Test Users API"""

from datetime import datetime
from json import loads

from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.brands.models import Brand
from authentik.core.models import (
    USER_ATTRIBUTE_TOKEN_EXPIRING,
    AuthenticatedSession,
    Session,
    Token,
    User,
    UserTypes,
)
from authentik.core.tests.utils import (
    create_test_admin_user,
    create_test_brand,
    create_test_flow,
    create_test_user,
)
from authentik.flows.models import FlowAuthenticationRequirement, FlowDesignation
from authentik.lib.generators import generate_id, generate_key
from authentik.stages.email.models import EmailStage


class TestUsersAPI(APITestCase):
    """Test Users API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()

    def test_filter_type(self):
        """Test API filtering by type"""
        self.client.force_login(self.admin)
        user = create_test_admin_user(type=UserTypes.EXTERNAL)
        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={
                "type": UserTypes.EXTERNAL,
                "username": user.username,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_is_superuser(self):
        """Test API filtering by superuser status"""
        User.objects.all().delete()
        admin = create_test_admin_user()
        self.client.force_login(admin)
        # Test superuser
        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={
                "is_superuser": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["username"], admin.username)
        # Test non-superuser
        user = create_test_user()
        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={
                "is_superuser": False,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(len(body["results"]), 1, body)
        self.assertEqual(body["results"][0]["username"], user.username)

    def test_list_with_groups(self):
        """Test listing with groups"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-list"), {"include_groups": "true"})
        self.assertEqual(response.status_code, 200)

    def test_recovery_no_flow(self):
        """Test user recovery link (no recovery flow set)"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-recovery", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"non_field_errors": "No recovery flow set."})

    def test_set_password(self):
        """Test Direct password set"""
        self.client.force_login(self.admin)
        new_pw = generate_key()
        response = self.client.post(
            reverse("authentik_api:user-set-password", kwargs={"pk": self.admin.pk}),
            data={"password": new_pw},
        )
        self.assertEqual(response.status_code, 204)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password(new_pw))

    def test_set_password_blank(self):
        """Test Direct password set"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-set-password", kwargs={"pk": self.admin.pk}),
            data={"password": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"password": ["This field may not be blank."]})

    def test_recovery(self):
        """Test user recovery link"""
        flow = create_test_flow(
            FlowDesignation.RECOVERY,
            authentication=FlowAuthenticationRequirement.REQUIRE_UNAUTHENTICATED,
        )
        brand: Brand = create_test_brand()
        brand.flow_recovery = flow
        brand.save()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-recovery", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_recovery_email_no_flow(self):
        """Test user recovery link (no recovery flow set)"""
        self.client.force_login(self.admin)
        self.user.email = ""
        self.user.save()
        stage = EmailStage.objects.create(name="email")
        response = self.client.post(
            reverse("authentik_api:user-recovery-email", kwargs={"pk": self.user.pk})
            + f"?email_stage={stage.pk}"
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content, {"non_field_errors": "User does not have an email address set."}
        )
        self.user.email = "foo@bar.baz"
        self.user.save()
        response = self.client.post(
            reverse("authentik_api:user-recovery-email", kwargs={"pk": self.user.pk})
            + f"?email_stage={stage.pk}"
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"non_field_errors": "No recovery flow set."})

    def test_recovery_email_no_stage(self):
        """Test user recovery link (no email stage)"""
        self.user.email = "foo@bar.baz"
        self.user.save()
        flow = create_test_flow(designation=FlowDesignation.RECOVERY)
        brand: Brand = create_test_brand()
        brand.flow_recovery = flow
        brand.save()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-recovery-email", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"non_field_errors": "Email stage does not exist."})

    def test_recovery_email(self):
        """Test user recovery link"""
        self.user.email = "foo@bar.baz"
        self.user.save()
        flow = create_test_flow(FlowDesignation.RECOVERY)
        brand: Brand = create_test_brand()
        brand.flow_recovery = flow
        brand.save()

        stage = EmailStage.objects.create(name="email")

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "authentik_api:user-recovery-email",
                kwargs={"pk": self.user.pk},
            )
            + f"?email_stage={stage.pk}"
        )
        self.assertEqual(response.status_code, 204)

    def test_service_account(self):
        """Service account creation"""
        self.client.force_login(self.admin)
        response = self.client.post(reverse("authentik_api:user-service-account"))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 200)

        user_filter = User.objects.filter(
            username="test-sa",
            type=UserTypes.SERVICE_ACCOUNT,
            attributes={USER_ATTRIBUTE_TOKEN_EXPIRING: True},
        )
        self.assertTrue(user_filter.exists())
        user: User = user_filter.first()
        self.assertFalse(user.has_usable_password())

        token_filter = Token.objects.filter(user=user)
        self.assertTrue(token_filter.exists())
        self.assertTrue(token_filter.first().expiring)

    def test_service_account_no_expire(self):
        """Service account creation without token expiration"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
                "expiring": False,
            },
        )
        self.assertEqual(response.status_code, 200)

        user_filter = User.objects.filter(
            username="test-sa",
            type=UserTypes.SERVICE_ACCOUNT,
            attributes={USER_ATTRIBUTE_TOKEN_EXPIRING: False},
        )
        self.assertTrue(user_filter.exists())
        user: User = user_filter.first()
        self.assertFalse(user.has_usable_password())

        token_filter = Token.objects.filter(user=user)
        self.assertTrue(token_filter.exists())
        self.assertFalse(token_filter.first().expiring)

    def test_service_account_with_custom_expire(self):
        """Service account creation with custom token expiration date"""
        self.client.force_login(self.admin)
        expire_on = datetime(2050, 11, 11, 11, 11, 11).astimezone()
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
                "expires": expire_on.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200)

        user_filter = User.objects.filter(
            username="test-sa",
            type=UserTypes.SERVICE_ACCOUNT,
            attributes={USER_ATTRIBUTE_TOKEN_EXPIRING: True},
        )
        self.assertTrue(user_filter.exists())
        user: User = user_filter.first()
        self.assertFalse(user.has_usable_password())

        token_filter = Token.objects.filter(user=user)
        self.assertTrue(token_filter.exists())
        token = token_filter.first()
        self.assertTrue(token.expiring)
        self.assertEqual(token.expires, expire_on)

    def test_service_account_invalid(self):
        """Service account creation (twice with same name, expect error)"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 200)

        user_filter = User.objects.filter(
            username="test-sa",
            type=UserTypes.SERVICE_ACCOUNT,
            attributes={USER_ATTRIBUTE_TOKEN_EXPIRING: True},
        )
        self.assertTrue(user_filter.exists())
        user: User = user_filter.first()
        self.assertFalse(user.has_usable_password())

        token_filter = Token.objects.filter(user=user)
        self.assertTrue(token_filter.exists())
        self.assertTrue(token_filter.first().expiring)

        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_paths(self):
        """Test path"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-paths"),
        )
        self.assertEqual(response.status_code, 200)
        expected = list(
            User.objects.all()
            .values("path")
            .distinct()
            .order_by("path")
            .values_list("path", flat=True)
        )
        self.assertJSONEqual(response.content.decode(), {"paths": expected})

    def test_path_valid(self):
        """Test path"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"name": generate_id(), "username": generate_id(), "groups": [], "path": "foo"},
        )
        self.assertEqual(response.status_code, 201)

    def test_path_invalid(self):
        """Test path (invalid)"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"name": generate_id(), "username": generate_id(), "groups": [], "path": "/foo"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(), {"path": ["No leading or trailing slashes allowed."]}
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"name": generate_id(), "username": generate_id(), "groups": [], "path": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content.decode(), {"path": ["This field may not be blank."]})

        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"name": generate_id(), "username": generate_id(), "groups": [], "path": "foo/"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(), {"path": ["No leading or trailing slashes allowed."]}
        )

        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={
                "name": generate_id(),
                "username": generate_id(),
                "groups": [],
                "path": "fos//o",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(), {"path": ["No empty segments in user path allowed."]}
        )

    def test_me(self):
        """Test user's me endpoint"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)

    def test_session_delete(self):
        """Ensure sessions are deleted when a user is deactivated"""
        user = create_test_admin_user()
        session_id = generate_id()
        session = Session.objects.create(
            session_key=session_id,
            last_ip="255.255.255.255",
            last_user_agent="",
        )
        AuthenticatedSession.objects.create(
            session=session,
            user=user,
        )

        self.client.force_login(self.admin)
        response = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": user.pk}),
            data={
                "is_active": False,
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertFalse(Session.objects.filter(session_key=session_id).exists())
        self.assertFalse(
            AuthenticatedSession.objects.filter(session__session_key=session_id).exists()
        )

    def test_sort_by_last_updated(self):
        """Test API sorting by last_updated"""
        User.objects.all().delete()
        admin = create_test_admin_user()
        self.client.force_login(admin)

        user = create_test_user()
        admin.first_name = "Sample change"
        admin.last_name = "To trigger an update"
        admin.save()

        # Ascending
        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={
                "ordering": "last_updated",
            },
        )
        self.assertEqual(response.status_code, 200)

        body = loads(response.content)
        self.assertEqual(len(body["results"]), 2)
        self.assertEqual(body["results"][0]["pk"], user.pk)

        # Descending
        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={
                "ordering": "-last_updated",
            },
        )
        self.assertEqual(response.status_code, 200)

        body = loads(response.content)
        self.assertEqual(len(body["results"]), 2)
        self.assertEqual(body["results"][0]["pk"], admin.pk)

    def test_sort_by_date_joined(self):
        """Test API sorting by date_joined"""
        User.objects.all().delete()
        admin = create_test_admin_user()
        self.client.force_login(admin)

        user = create_test_user()

        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={
                "ordering": "date_joined",
            },
        )
        self.assertEqual(response.status_code, 200)

        body = loads(response.content)
        self.assertEqual(len(body["results"]), 2)
        self.assertEqual(body["results"][0]["pk"], admin.pk)

        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={
                "ordering": "-date_joined",
            },
        )
        self.assertEqual(response.status_code, 200)

        body = loads(response.content)
        self.assertEqual(len(body["results"]), 2)
        self.assertEqual(body["results"][0]["pk"], user.pk)

    def test_service_account_validation_empty_username(self):
        """Test service account creation with empty/blank username validation"""
        self.client.force_login(self.admin)

        # Test with empty string
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"name": ["This field may not be blank."]},
        )

        # Test with only whitespace
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "   ",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"name": ["This field may not be blank."]},
        )

        # Test with tab and newline characters
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "\t\n",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"name": ["This field may not be blank."]},
        )

    def test_service_account_validation_valid_username(self):
        """Test service account creation with valid username"""
        self.client.force_login(self.admin)

        # Test with valid username
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "valid-service-account",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 200)

        # Verify response structure
        body = loads(response.content)
        self.assertIn("username", body)
        self.assertIn("user_uid", body)
        self.assertIn("user_pk", body)
        self.assertIn("group_pk", body)  # Should exist since create_group=True
        self.assertIn("token", body)

        # Verify field types
        self.assertEqual(body["username"], "valid-service-account")
        self.assertIsInstance(body["user_pk"], int)
        self.assertIsInstance(body["user_uid"], str)
        self.assertIsInstance(body["token"], str)
        self.assertIsInstance(body["group_pk"], str)

    def test_service_account_validation_without_group(self):
        """Test service account creation without creating a group"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "no-group-service-account",
                "create_group": False,
            },
        )
        self.assertEqual(response.status_code, 200)

        body = loads(response.content)
        self.assertIn("username", body)
        self.assertIn("user_uid", body)
        self.assertIn("user_pk", body)
        self.assertIn("token", body)
        # Should NOT have group_pk when create_group=False
        self.assertNotIn("group_pk", body)

    def test_service_account_validation_duplicate_username(self):
        """Test service account creation with duplicate username"""
        self.client.force_login(self.admin)

        # Create first service account
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "duplicate-test",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 200)

        # Attempt to create second with same username
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "duplicate-test",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"name": ["This field must be unique."]},
        )

    def test_service_account_validation_invalid_create_group(self):
        """Test service account creation with invalid create_group field"""
        self.client.force_login(self.admin)

        # Test with string instead of boolean
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": "invalid",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"create_group": ["Must be a valid boolean."]},
        )

        # Test with number instead of boolean
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": 123,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"create_group": ["Must be a valid boolean."]},
        )

    def test_service_account_validation_invalid_expiring(self):
        """Test service account creation with invalid expiring field"""
        self.client.force_login(self.admin)

        # Test with string instead of boolean
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "expiring": "invalid",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"expiring": ["Must be a valid boolean."]},
        )

    def test_service_account_validation_invalid_expires(self):
        """Test service account creation with invalid expires field"""
        self.client.force_login(self.admin)

        # Test with invalid datetime string
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "expires": "invalid-datetime",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {
                "expires": [
                    "Datetime has wrong format. Use one of these formats instead: "
                    "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]."
                ]
            },
        )

        # Test with invalid format
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "expires": "2024-13-45",  # Invalid month/day
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {
                "expires": [
                    "Datetime has wrong format. Use one of these formats instead: "
                    "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]."
                ]
            },
        )

    def test_service_account_validation_multiple_errors(self):
        """Test service account creation with multiple validation errors"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "",  # Empty username
                "create_group": "invalid",  # Invalid boolean
                "expiring": 123,  # Invalid boolean
                "expires": "not-a-date",  # Invalid datetime
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {
                "name": ["This field may not be blank."],
                "create_group": ["Must be a valid boolean."],
                "expiring": ["Must be a valid boolean."],
                "expires": [
                    "Datetime has wrong format. Use one of these formats instead: "
                    "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]."
                ],
            },
        )

    def test_service_account_validation_user_friendly_duplicate_error(self):
        """Test that duplicate username returns user-friendly error, not database error"""
        self.client.force_login(self.admin)

        # Create first service account
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "duplicate-username-test",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 200)

        # Attempt to create second with same username
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "duplicate-username-test",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"name": ["This field must be unique."]},
        )

    def test_filter_last_login(self):
        """Test API filtering by last_login"""
        from datetime import timedelta

        from django.utils import timezone

        User.objects.all().delete()
        admin = create_test_admin_user()
        self.client.force_login(admin)

        # Create users with different last_login values
        user_recent = create_test_user()
        user_recent.last_login = timezone.now()
        user_recent.save()

        user_old = create_test_user()
        user_old.last_login = timezone.now() - timedelta(days=400)  # Over 1 year ago
        user_old.save()

        user_never = create_test_user()
        user_never.last_login = None  # Never logged in
        user_never.save()

        # Filter users who logged in before 1 year ago
        one_year_ago = (timezone.now() - timedelta(days=365)).isoformat()
        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={"last_login__lt": one_year_ago},
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["pk"], user_old.pk)

        # Filter users who have never logged in
        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={"last_login__isnull": True},
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        # Should include user_never and admin (who hasn't logged in via the app)
        pks = [r["pk"] for r in body["results"]]
        self.assertIn(user_never.pk, pks)

    def test_sort_by_last_login(self):
        """Test API sorting by last_login"""
        from datetime import timedelta

        from django.utils import timezone

        User.objects.all().delete()
        admin = create_test_admin_user()
        self.client.force_login(admin)

        user1 = create_test_user()
        user1.last_login = timezone.now() - timedelta(days=10)
        user1.save()

        user2 = create_test_user()
        user2.last_login = timezone.now() - timedelta(days=5)
        user2.save()

        # Ascending order (oldest first)
        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={"ordering": "last_login"},
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        # Users with null last_login come first, then user1 (older), then user2 (newer)
        self.assertEqual(len(body["results"]), 3)

        # Descending order (newest first)
        response = self.client.get(
            reverse("authentik_api:user-list"),
            data={"ordering": "-last_login"},
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        # user2 should come before user1 (more recent login)
        pks = [r["pk"] for r in body["results"]]
        self.assertIn(user1.pk, pks)
        self.assertIn(user2.pk, pks)
        # Verify user2 comes before user1 in descending order
        self.assertLess(pks.index(user2.pk), pks.index(user1.pk))
