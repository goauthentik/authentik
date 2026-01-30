"""Test Users Account Lockdown API"""

from json import loads
from unittest.mock import MagicMock, patch

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from authentik.core.models import AuthenticatedSession, Session, Token, TokenIntents, UserTypes
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider, RefreshToken
from authentik.tenants.models import Tenant

# Patch for enterprise license check
patch_license = patch(
    "authentik.enterprise.models.LicenseUsageStatus.is_valid",
    MagicMock(return_value=True),
)


@patch_license
class TestUsersAccountLockdownAPI(APITestCase):
    """Test Users Account Lockdown API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()
        self.user.email = f"{generate_id()}@test.com"
        self.user.save()
        self.tenant = Tenant.objects.first()
        self.tenant.account_lockdown_enabled = True
        self.tenant.save()

    def test_account_lockdown_success(self):
        """Test successful account lockdown trigger"""
        self.client.force_login(self.admin)
        old_password = self.user.password

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk, "reason": "Compromised account"},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

        # Verify user was deactivated and password changed
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertNotEqual(self.user.password, old_password)

    def test_account_lockdown_creates_event(self):
        """Test that account lockdown creates an event"""
        self.client.force_login(self.admin)
        Event.objects.all().delete()

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk, "reason": "Security incident"},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

        # Verify event was created
        event = Event.objects.filter(action=EventAction.ACCOUNT_LOCKDOWN_TRIGGERED).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["reason"], "Security incident")
        self.assertEqual(event.context["affected_user"], self.user.username)
        self.assertEqual(event.user["username"], self.admin.username)

    def test_account_lockdown_deletes_sessions(self):
        """Test that account lockdown deletes user sessions"""
        self.client.force_login(self.admin)

        # Create a session for the target user
        session_id = generate_id()
        session = Session.objects.create(
            session_key=session_id,
            last_ip="127.0.0.1",
            last_user_agent="test",
        )
        AuthenticatedSession.objects.create(session=session, user=self.user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk, "reason": "Session hijack"},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

        # Verify session was deleted
        self.assertFalse(Session.objects.filter(session_key=session_id).exists())

    def test_account_lockdown_revokes_tokens(self):
        """Test that account lockdown revokes all user tokens"""
        self.client.force_login(self.admin)

        # Create tokens for the target user
        Token.objects.create(
            identifier="test-api-token",
            user=self.user,
            intent=TokenIntents.INTENT_API,
        )
        Token.objects.create(
            identifier="test-app-password",
            user=self.user,
            intent=TokenIntents.INTENT_APP_PASSWORD,
        )

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk, "reason": "Token compromise"},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

        # Verify tokens were deleted
        self.assertEqual(Token.objects.filter(user=self.user).count(), 0)

    def test_account_lockdown_revokes_oauth2_tokens(self):
        """Test that account lockdown revokes OAuth2 access and refresh tokens"""
        self.client.force_login(self.admin)

        # Create a minimal OAuth2 provider for the tokens
        provider = OAuth2Provider.objects.create(
            name=f"test-provider-{generate_id()}",
            client_id=generate_id(),
            authorization_flow=None,
        )

        # Create OAuth2 tokens for the target user
        AccessToken.objects.create(
            user=self.user,
            provider=provider,
            token=generate_id(),
            auth_time=now(),
            _id_token="{}",
        )
        RefreshToken.objects.create(
            user=self.user,
            provider=provider,
            token=generate_id(),
            auth_time=now(),
        )

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk, "reason": "OAuth2 token compromise"},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

        # Verify OAuth2 tokens were deleted
        self.assertEqual(AccessToken.objects.filter(user=self.user).count(), 0)
        self.assertEqual(RefreshToken.objects.filter(user=self.user).count(), 0)

    def test_account_lockdown_disabled(self):
        """Test account lockdown when feature is disabled"""
        self.tenant.account_lockdown_enabled = False
        self.tenant.save()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk, "reason": "Test"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("Account lockdown feature is disabled", body["non_field_errors"][0])

    def test_account_lockdown_unauthenticated(self):
        """Test account lockdown requires authentication"""
        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk, "reason": "Test"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_account_lockdown_non_admin(self):
        """Test account lockdown requires admin permissions"""
        regular_user = create_test_user()
        self.client.force_login(regular_user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"user": self.user.pk, "reason": "Test"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)


@patch_license
class TestUsersAccountLockdownSelfServiceAPI(APITestCase):
    """Test Users Account Lockdown Self-Service API"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.user.email = f"{generate_id()}@test.com"
        self.user.save()
        self.tenant = Tenant.objects.first()
        self.tenant.account_lockdown_enabled = True
        self.tenant.save()

    def test_account_lockdown_self_success(self):
        """Test successful self-service account lockdown"""
        self.client.force_login(self.user)
        old_password = self.user.password

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"reason": "I think my account was compromised"},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

        # Verify user was deactivated and password changed
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertNotEqual(self.user.password, old_password)

    def test_account_lockdown_self_creates_event(self):
        """Test that self-service lockdown creates correct event"""
        self.client.force_login(self.user)
        Event.objects.all().delete()

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"reason": "Security incident"},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

        # Verify event was created - for self-service, event.user is the user themselves
        event = Event.objects.filter(action=EventAction.ACCOUNT_LOCKDOWN_TRIGGERED).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["reason"], "Security incident")
        self.assertEqual(event.context["affected_user"], self.user.username)
        self.assertEqual(event.user["username"], self.user.username)

    def test_account_lockdown_self_deletes_sessions(self):
        """Test that self-service lockdown deletes user sessions"""
        self.client.force_login(self.user)

        # Create a session for the user
        session_id = generate_id()
        session = Session.objects.create(
            session_key=session_id,
            last_ip="127.0.0.1",
            last_user_agent="test",
        )
        AuthenticatedSession.objects.create(session=session, user=self.user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"reason": "Session hijack suspected"},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

        # Verify session was deleted
        self.assertFalse(Session.objects.filter(session_key=session_id).exists())

    def test_account_lockdown_self_revokes_tokens(self):
        """Test that self-service lockdown revokes all user tokens"""
        self.client.force_login(self.user)

        # Create tokens for the user
        Token.objects.create(
            identifier="test-api-token",
            user=self.user,
            intent=TokenIntents.INTENT_API,
        )
        Token.objects.create(
            identifier="test-app-password",
            user=self.user,
            intent=TokenIntents.INTENT_APP_PASSWORD,
        )

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"reason": "Token compromise"},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

        # Verify tokens were deleted
        self.assertEqual(Token.objects.filter(user=self.user).count(), 0)

    def test_account_lockdown_self_disabled(self):
        """Test self-service lockdown when feature is disabled"""
        self.tenant.account_lockdown_enabled = False
        self.tenant.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"reason": "Test"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("Account lockdown feature is disabled", body["non_field_errors"][0])

    def test_account_lockdown_self_internal_service_account_denied(self):
        """Test that internal service accounts cannot use self-lockdown"""
        internal_sa = create_test_user()
        internal_sa.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        internal_sa.save()
        self.client.force_login(internal_sa)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"reason": "Test"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn(
            "Cannot trigger account lockdown on internal service accounts",
            body["non_field_errors"][0],
        )

    def test_account_lockdown_self_requires_reason(self):
        """Test that reason field is required"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("reason", body)

    def test_account_lockdown_self_unauthenticated(self):
        """Test self-service lockdown requires authentication"""
        response = self.client.post(
            reverse("authentik_api:user-account-lockdown"),
            data={"reason": "Test"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)


@patch_license
class TestUsersAccountLockdownBulkAPI(APITestCase):
    """Test Users Account Lockdown Bulk API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user1 = create_test_user()
        self.user1.email = f"{generate_id()}@test.com"
        self.user1.save()
        self.user2 = create_test_user()
        self.user2.email = f"{generate_id()}@test.com"
        self.user2.save()
        self.tenant = Tenant.objects.first()
        self.tenant.account_lockdown_enabled = True
        self.tenant.save()

    def test_account_lockdown_bulk_success(self):
        """Test successful bulk account lockdown trigger"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown-bulk"),
            data={
                "users": [self.user1.pk, self.user2.pk],
                "reason": "Bulk security incident",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        body = loads(response.content)

        # Verify response contains processed info
        self.assertIn("processed", body)
        self.assertIn("skipped", body)
        self.assertEqual(len(body["processed"]), 2)
        self.assertEqual(len(body["skipped"]), 0)

        # Verify both users were deactivated
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertFalse(self.user1.is_active)
        self.assertFalse(self.user2.is_active)

    def test_account_lockdown_bulk_creates_events(self):
        """Test that bulk account lockdown creates events for each user"""
        self.client.force_login(self.admin)
        Event.objects.all().delete()

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown-bulk"),
            data={
                "users": [self.user1.pk, self.user2.pk],
                "reason": "Bulk incident",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        # Verify events were created for each user
        events = Event.objects.filter(action=EventAction.ACCOUNT_LOCKDOWN_TRIGGERED)
        self.assertEqual(events.count(), 2)

        usernames = {event.context["affected_user"] for event in events}
        self.assertIn(self.user1.username, usernames)
        self.assertIn(self.user2.username, usernames)

    def test_account_lockdown_bulk_skips_self(self):
        """Test that bulk account lockdown skips the requesting user and reports it"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown-bulk"),
            data={
                "users": [self.user1.pk, self.admin.pk],
                "reason": "Bulk test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        body = loads(response.content)

        # Verify admin was skipped and reported
        self.assertEqual(len(body["processed"]), 1)
        self.assertEqual(len(body["skipped"]), 1)
        self.assertEqual(body["skipped"][0]["username"], self.admin.username)

        # Verify admin was not affected
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

        # Verify other user was affected
        self.user1.refresh_from_db()
        self.assertFalse(self.user1.is_active)

    def test_account_lockdown_bulk_skips_internal_service_accounts(self):
        """Test that bulk lockdown skips internal service accounts and reports it"""
        self.client.force_login(self.admin)

        # Create an internal service account
        internal_sa = create_test_user()
        internal_sa.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        internal_sa.save()

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown-bulk"),
            data={
                "users": [self.user1.pk, internal_sa.pk],
                "reason": "Bulk test with SA",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        body = loads(response.content)

        # Verify internal SA was skipped and reported
        self.assertEqual(len(body["processed"]), 1)
        self.assertEqual(len(body["skipped"]), 1)
        self.assertEqual(body["skipped"][0]["username"], internal_sa.username)
        self.assertIn("cannot be locked down", body["skipped"][0]["reason"].lower())

        # Verify internal SA was not affected
        internal_sa.refresh_from_db()
        self.assertTrue(internal_sa.is_active)

    def test_account_lockdown_bulk_disabled(self):
        """Test bulk account lockdown when feature is disabled"""
        self.tenant.account_lockdown_enabled = False
        self.tenant.save()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("authentik_api:user-account-lockdown-bulk"),
            data={
                "users": [self.user1.pk],
                "reason": "Test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = loads(response.content)
        self.assertIn("Account lockdown feature is disabled", body["non_field_errors"][0])
