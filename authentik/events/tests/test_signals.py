"""Tests for login-event lookup."""

from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.utils.timezone import now
from rest_framework.request import Request

from authentik.core.models import Session
from authentik.core.sessions import SessionStore
from authentik.core.tests.utils import create_test_session, create_test_user
from authentik.events.models import Event, EventAction
from authentik.events.signals import SESSION_LOGIN_EVENT, get_login_event
from authentik.lib.generators import generate_id
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD


class TestGetLoginEvent(TestCase):
    """Historical login metadata is independent of browser session selection."""

    def setUp(self):
        self.switching_token = generate_id(32)
        self.session = create_test_session(create_test_user(), self.switching_token)
        self.event = Event.new(EventAction.LOGIN, **{PLAN_CONTEXT_METHOD: "password"})
        store = SessionStore(self.session.session_id)
        store[SESSION_LOGIN_EVENT] = self.event
        store.save()

    def test_expired_session(self):
        """Expired records do not supply login metadata."""
        Session.objects.filter(pk=self.session.session_id).update(
            expires=now() - timedelta(seconds=1)
        )
        self.assertIsNone(get_login_event(self.session))

    def test_deleted_session(self):
        """A deleted record does not supply metadata through a cached relation."""
        Session.objects.filter(pk=self.session.session_id).delete()
        self.assertIsNone(get_login_event(self.session))

    def test_request(self):
        """Request lookups continue to use the request's session store."""
        request = RequestFactory().get("/")
        request.session = SessionStore(self.session.session_id)
        self.assertEqual(get_login_event(request), self.event)
        self.assertEqual(get_login_event(Request(request)), self.event)

        create_test_session(create_test_user(), self.switching_token)
        request.session = SessionStore(self.session.session_id)
        self.assertIsNone(get_login_event(request))
        self.assertIsNone(get_login_event(Request(request)))
