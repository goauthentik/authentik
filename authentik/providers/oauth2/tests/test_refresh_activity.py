"""Successful refresh activity sampling must not alter interactive login claims."""

from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from json import dumps
from threading import Barrier
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time

from authentik.common.oauth.constants import GRANT_TYPE_REFRESH_TOKEN
from authentik.core.middleware import (
    SESSION_KEY_IMPERSONATE_ORIGINAL_USER,
    SESSION_KEY_IMPERSONATE_USER,
)
from authentik.core.models import Application, AuthenticatedSession, Session, User
from authentik.core.sessions import SessionStore
from authentik.core.tests.utils import create_test_cert, create_test_flow, create_test_user
from authentik.enterprise.lifecycle.expiration.models import ActivityBasis, UserExpirationRule
from authentik.enterprise.lifecycle.offboarding.models import UserOffboarding
from authentik.enterprise.lifecycle.offboarding.tasks import execute_offboarding
from authentik.enterprise.tests import enterprise_test
from authentik.events.activity import REFRESH_ACTIVITY_INTERVAL
from authentik.events.models import Event, EventAction
from authentik.events.signals import SESSION_LOGIN_EVENT, get_login_event
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    GrantType,
    OAuth2Provider,
    RefreshToken,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class RefreshActivityMixin:
    def setUp(self):
        super().setUp()
        self.user = create_test_user()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.REFRESH_TOKEN],
            signing_key=self.keypair,
            refresh_token_threshold="seconds=0",
        )
        self.provider.property_mappings.add(
            ScopeMapping.objects.create(
                name=generate_id(), scope_name="offline_access", expression="return {}"
            )
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=self.provider)
        self.token = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            _id_token=dumps({}),
            auth_time=now() - timedelta(days=10),
            _scope="offline_access",
            expires=now() + timedelta(days=30),
        )
        self.header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()

    def _refresh(self, token=None):
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": (token or self.token).token,
            },
            HTTP_AUTHORIZATION=f"Basic {self.header}",
        )
        return response


class TestRefreshActivity(RefreshActivityMixin, OAuthTestCase):
    def test_rotation_and_no_rotation_record_activity(self):
        for rotate in (False, True):
            with self.subTest(rotate=rotate):
                Event.objects.filter(action=EventAction.TOKEN_REFRESH).delete()
                self.provider.refresh_token_threshold = "seconds=0" if rotate else "seconds=1"
                self.provider.save()
                last_login = self.user.last_login
                response = self._refresh()
                self.assertEqual(response.status_code, 200)
                self.assertEqual("refresh_token" in response.json(), rotate)
                event = Event.objects.get(action=EventAction.TOKEN_REFRESH, user__pk=self.user.pk)
                self.assertEqual(event.context["grant_type"], GRANT_TYPE_REFRESH_TOKEN)
                self.assertEqual(event.context["provider"]["pk"], self.provider.pk)
                self.assertFalse(
                    Event.objects.filter(action=EventAction.LOGIN, user__pk=self.user.pk).exists()
                )
                self.user.refresh_from_db()
                self.assertEqual(self.user.last_login, last_login)
                access = AccessToken.objects.get(token=response.json()["access_token"])
                self.assertEqual(access.auth_time, self.token.auth_time)
                self.assertEqual(access.id_token.auth_time, int(self.token.auth_time.timestamp()))

    def test_recording_interval_boundary(self):
        self.provider.refresh_token_threshold = "seconds=1"
        self.provider.save()
        with freeze_time() as clock:
            self.assertEqual(self._refresh().status_code, 200)
            recorded_at = now()
            for offset, count in ((-1, 1), (0, 2), (1, 2)):
                clock.move_to(
                    recorded_at + REFRESH_ACTIVITY_INTERVAL + timedelta(microseconds=offset)
                )
                self.assertEqual(self._refresh().status_code, 200)
                self.assertEqual(
                    Event.objects.filter(action=EventAction.TOKEN_REFRESH).count(), count
                )

    def test_exact_login_does_not_suppress_first_refresh(self):
        Event.new(EventAction.LOGIN).set_user(self.user).save()
        self.assertEqual(self._refresh().status_code, 200)
        self.assertEqual(Event.objects.filter(action=EventAction.TOKEN_REFRESH).count(), 1)

    @enterprise_test()
    def test_throttled_refresh_after_basis_change_postpones_pending(self):
        self.provider.refresh_token_threshold = "seconds=1"
        self.provider.save()
        with (
            freeze_time() as clock,
            patch(
                "authentik.enterprise.lifecycle.expiration.tasks.apply_expiration_rule.send_with_options"
            ),
        ):
            User.objects.filter(pk=self.user.pk).update(
                last_login=now() - timedelta(days=100),
                date_joined=now() - timedelta(days=101),
            )
            self.assertEqual(self._refresh().status_code, 200)
            recorded_at = now()
            clock.tick(timedelta(seconds=1))
            rule = UserExpirationRule.objects.create(
                name=generate_id(), enabled=True, activity_basis=ActivityBasis.LAST_LOGIN
            )
            self.assertEqual(rule.apply(), 1)
            row = UserOffboarding.objects.get(user=self.user)
            original_due = row.scheduled_at
            clock.tick(timedelta(seconds=1))
            self.assertEqual(self._refresh().status_code, 200)
            self.assertEqual(Event.objects.filter(action=EventAction.TOKEN_REFRESH).count(), 1)
            rule.activity_basis = ActivityBasis.SUCCESSFUL_EVENTS
            rule.save()
            execute_offboarding(str(row.pk))
            row.refresh_from_db()
            due = recorded_at + REFRESH_ACTIVITY_INTERVAL + timedelta(days=90)
            self.assertGreater(row.scheduled_at, original_due)
            self.assertEqual(row.scheduled_at, due)
            clock.move_to(due - timedelta(microseconds=1))
            execute_offboarding(str(row.pk))
            self.user.refresh_from_db()
            self.assertTrue(self.user.is_active)
            clock.move_to(due)
            execute_offboarding(str(row.pk))
            self.user.refresh_from_db()
            self.assertFalse(self.user.is_active)

    @enterprise_test()
    def test_throttled_refresh_before_takeover_keeps_pending_with_allowance(self):
        self.provider.refresh_token_threshold = "seconds=1"
        self.provider.save()
        with (
            freeze_time() as clock,
            patch(
                "authentik.enterprise.lifecycle.expiration.tasks.apply_expiration_rule.send_with_options"
            ),
        ):
            User.objects.filter(pk=self.user.pk).update(
                last_login=now() - timedelta(days=100),
                date_joined=now() - timedelta(days=101),
            )
            self.assertEqual(self._refresh().status_code, 200)
            recorded_at = now()
            clock.tick(timedelta(seconds=1))
            owner = UserExpirationRule.objects.create(
                name=generate_id(), enabled=True, activity_basis=ActivityBasis.LAST_LOGIN
            )
            self.assertEqual(owner.apply(), 1)
            row = UserOffboarding.objects.get(user=self.user)
            original_created = row.created_at
            clock.tick(timedelta(seconds=1))
            self.assertEqual(self._refresh().status_code, 200)
            self.assertEqual(Event.objects.filter(action=EventAction.TOKEN_REFRESH).count(), 1)
            # A queued execution observes a less strict owner and resolves the
            # earlier event-based winner, retaining the row's original creation time.
            owner.inactivity_duration = "days=130"
            owner.save()
            winner = UserExpirationRule.objects.create(
                name=generate_id(), enabled=True, inactivity_duration="minutes=30"
            )
            execute_offboarding(str(row.pk))
            row.refresh_from_db()
            due = recorded_at + REFRESH_ACTIVITY_INTERVAL + timedelta(minutes=30)
            self.assertEqual(row.rule, winner)
            self.assertEqual(row.created_at, original_created)
            self.assertEqual(row.scheduled_at, due)
            clock.tick(timedelta(seconds=1))
            self.assertEqual(self._refresh().status_code, 200)
            self.assertEqual(Event.objects.filter(action=EventAction.TOKEN_REFRESH).count(), 1)
            execute_offboarding(str(row.pk))
            row.refresh_from_db()
            self.assertEqual(row.scheduled_at, due)
            clock.move_to(due - timedelta(microseconds=1))
            execute_offboarding(str(row.pk))
            self.user.refresh_from_db()
            self.assertTrue(self.user.is_active)
            clock.move_to(due)
            execute_offboarding(str(row.pk))
            self.user.refresh_from_db()
            self.assertFalse(self.user.is_active)

    def test_revoked_refresh_does_not_record_success(self):
        self.token.revoked = True
        self.token.save()
        self.assertEqual(self._refresh().status_code, 400)
        self.assertFalse(Event.objects.filter(action=EventAction.TOKEN_REFRESH).exists())
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.SUSPICIOUS_REQUEST, user__pk=self.user.pk
            ).exists()
        )

    def test_refresh_while_impersonating_does_not_record_activity(self):
        session = self.client.session
        session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER] = create_test_user()
        session[SESSION_KEY_IMPERSONATE_USER] = create_test_user()
        session.save()
        self.assertEqual(self._refresh().status_code, 200)
        self.assertFalse(Event.objects.filter(action=EventAction.TOKEN_REFRESH).exists())

    def test_pending_flow_for_another_user_does_not_record_activity(self):
        self.provider.refresh_token_threshold = "seconds=1"
        self.provider.save()
        for pending_user in (create_test_user(), User(username=generate_id())):
            with self.subTest(saved=pending_user.pk is not None):
                session = self.client.session
                plan = FlowPlan(generate_id())
                plan.context[PLAN_CONTEXT_PENDING_USER] = pending_user
                session[SESSION_KEY_PLAN] = plan
                session.save()
                self.assertEqual(self._refresh().status_code, 200)
                self.assertFalse(Event.objects.filter(action=EventAction.TOKEN_REFRESH).exists())

    def test_pending_flow_for_token_user_preserves_recording_and_throttle(self):
        self.provider.refresh_token_threshold = "seconds=1"
        self.provider.save()
        session = self.client.session
        plan = FlowPlan(generate_id())
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session[SESSION_KEY_PLAN] = plan
        session.save()
        self.assertEqual(self._refresh().status_code, 200)
        self.assertEqual(self._refresh().status_code, 200)
        event = Event.objects.get(action=EventAction.TOKEN_REFRESH)
        self.assertEqual(event.user["pk"], self.user.pk)

    def test_invalid_scope_does_not_record_success(self):
        self.token.scope = ["openid"]
        self.token.save()
        self.assertEqual(self._refresh().status_code, 400)
        self.assertFalse(Event.objects.filter(action=EventAction.TOKEN_REFRESH).exists())

    def test_refresh_preserves_session_login_event_and_amr(self):
        login = Event.new(EventAction.LOGIN, auth_method="password").set_user(self.user)
        login.save()
        store = SessionStore()
        store[SESSION_LOGIN_EVENT] = login
        store.save()
        auth_session = AuthenticatedSession.objects.create(
            session=Session.objects.get(pk=store.session_key), user=self.user
        )
        self.token.session = auth_session
        self.token.save()
        response = self._refresh()
        self.assertEqual(response.status_code, 200)
        access = AccessToken.objects.get(token=response.json()["access_token"])
        self.assertEqual(access.session, auth_session)
        self.assertEqual(access.id_token.amr, ["pwd"])
        self.assertEqual(get_login_event(auth_session).pk, login.pk)
        self.assertEqual(
            Event.objects.filter(action=EventAction.LOGIN, user__pk=self.user.pk).count(), 1
        )


class TestConcurrentRefreshActivity(RefreshActivityMixin, TransactionTestCase):
    def setUp(self):
        self.keypair = create_test_cert()
        super().setUp()

    def test_concurrent_successes_can_record_duplicates(self):
        self.provider.refresh_token_threshold = "seconds=1"
        self.provider.save()
        barrier = Barrier(2)
        queryset_type = type(Event.objects.all())
        original_first = queryset_type.first

        def racing_first(queryset):
            result = original_first(queryset)
            if queryset.model is Event and "token_refresh" in str(queryset.query):
                # Both successful grants see the same missing refresh event.
                barrier.wait(timeout=10)
            return result

        def refresh():
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout = '20s'")
                response = Client().post(
                    reverse("authentik_providers_oauth2:token"),
                    data={
                        "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                        "refresh_token": self.token.token,
                    },
                    HTTP_AUTHORIZATION=f"Basic {self.header}",
                )
                return response.status_code
            finally:
                connection.close()

        with patch.object(queryset_type, "first", racing_first):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(refresh) for _ in range(2)]
                try:
                    self.assertEqual([future.result(timeout=30) for future in futures], [200, 200])
                finally:
                    barrier.abort()
        self.assertEqual(Event.objects.filter(action=EventAction.TOKEN_REFRESH).count(), 2)
        self.assertFalse(Event.objects.filter(action=EventAction.LOGIN).exists())
