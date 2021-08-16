"""Test Source flow_manager"""
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http.request import HttpRequest
from django.test import TestCase
from django.test.client import RequestFactory
from guardian.utils import get_anonymous_user

from authentik.core.models import SourceUserMatchingModes, User
from authentik.core.sources.flow_manager import Action
from authentik.flows.tests.test_planner import dummy_get_response
from authentik.providers.oauth2.generators import generate_client_id
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.views.callback import OAuthSourceFlowManager


class TestSourceFlowManager(TestCase):
    """Test Source flow_manager"""

    def setUp(self) -> None:
        super().setUp()
        self.source = OAuthSource.objects.create(name="test")
        self.factory = RequestFactory()
        self.identifier = generate_client_id()

    def get_request(self, user: User) -> HttpRequest:
        """Helper to create a get request with session and message middleware"""
        request = self.factory.get("/")
        request.user = user
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        middleware = MessageMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_unauthenticated_enroll(self):
        """Test un-authenticated user enrolling"""
        flow_manager = OAuthSourceFlowManager(
            self.source, self.get_request(AnonymousUser()), self.identifier, {}
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.ENROLL)
        flow_manager.get_flow()

    def test_unauthenticated_auth(self):
        """Test un-authenticated user authenticating"""
        UserOAuthSourceConnection.objects.create(
            user=get_anonymous_user(), source=self.source, identifier=self.identifier
        )

        flow_manager = OAuthSourceFlowManager(
            self.source, self.get_request(AnonymousUser()), self.identifier, {}
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.AUTH)
        flow_manager.get_flow()

    def test_authenticated_link(self):
        """Test authenticated user linking"""
        UserOAuthSourceConnection.objects.create(
            user=get_anonymous_user(), source=self.source, identifier=self.identifier
        )
        user = User.objects.create(username="foo", email="foo@bar.baz")
        flow_manager = OAuthSourceFlowManager(
            self.source, self.get_request(user), self.identifier, {}
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.LINK)
        flow_manager.get_flow()

    def test_unauthenticated_enroll_email(self):
        """Test un-authenticated user enrolling (link on email)"""
        User.objects.create(username="foo", email="foo@bar.baz")
        self.source.user_matching_mode = SourceUserMatchingModes.EMAIL_LINK

        # Without email, deny
        flow_manager = OAuthSourceFlowManager(
            self.source, self.get_request(AnonymousUser()), self.identifier, {}
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.DENY)
        flow_manager.get_flow()
        # With email
        flow_manager = OAuthSourceFlowManager(
            self.source,
            self.get_request(AnonymousUser()),
            self.identifier,
            {"email": "foo@bar.baz"},
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.LINK)
        flow_manager.get_flow()

    def test_unauthenticated_enroll_username(self):
        """Test un-authenticated user enrolling (link on username)"""
        User.objects.create(username="foo", email="foo@bar.baz")
        self.source.user_matching_mode = SourceUserMatchingModes.USERNAME_LINK

        # Without username, deny
        flow_manager = OAuthSourceFlowManager(
            self.source, self.get_request(AnonymousUser()), self.identifier, {}
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.DENY)
        flow_manager.get_flow()
        # With username
        flow_manager = OAuthSourceFlowManager(
            self.source,
            self.get_request(AnonymousUser()),
            self.identifier,
            {"username": "foo"},
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.LINK)
        flow_manager.get_flow()

    def test_unauthenticated_enroll_username_deny(self):
        """Test un-authenticated user enrolling (deny on username)"""
        User.objects.create(username="foo", email="foo@bar.baz")
        self.source.user_matching_mode = SourceUserMatchingModes.USERNAME_DENY

        # With non-existent username, enroll
        flow_manager = OAuthSourceFlowManager(
            self.source,
            self.get_request(AnonymousUser()),
            self.identifier,
            {
                "username": "bar",
            },
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.ENROLL)
        flow_manager.get_flow()
        # With username
        flow_manager = OAuthSourceFlowManager(
            self.source,
            self.get_request(AnonymousUser()),
            self.identifier,
            {"username": "foo"},
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.DENY)
        flow_manager.get_flow()

    def test_unauthenticated_enroll_link_non_existent(self):
        """Test un-authenticated user enrolling (link on username), username doesn't exist"""
        self.source.user_matching_mode = SourceUserMatchingModes.USERNAME_LINK

        flow_manager = OAuthSourceFlowManager(
            self.source,
            self.get_request(AnonymousUser()),
            self.identifier,
            {"username": "foo"},
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.ENROLL)
        flow_manager.get_flow()
