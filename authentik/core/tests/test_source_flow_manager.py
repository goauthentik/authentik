"""Test Source flow_manager"""
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from guardian.utils import get_anonymous_user

from authentik.core.models import SourceUserMatchingModes, User
from authentik.core.sources.flow_manager import Action
from authentik.core.tests.utils import create_test_flow
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import get_request
from authentik.policies.denied import AccessDeniedResponse
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.views.callback import OAuthSourceFlowManager


class TestSourceFlowManager(TestCase):
    """Test Source flow_manager"""

    def setUp(self) -> None:
        super().setUp()
        self.source: OAuthSource = OAuthSource.objects.create(name="test")
        self.identifier = generate_id()

    def test_unauthenticated_enroll(self):
        """Test un-authenticated user enrolling"""
        flow_manager = OAuthSourceFlowManager(
            self.source, get_request("/", user=AnonymousUser()), self.identifier, {}
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
            self.source, get_request("/", user=AnonymousUser()), self.identifier, {}
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
            self.source, get_request("/", user=user), self.identifier, {}
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
            self.source, get_request("/", user=AnonymousUser()), self.identifier, {}
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.DENY)
        flow_manager.get_flow()
        # With email
        flow_manager = OAuthSourceFlowManager(
            self.source,
            get_request("/", user=AnonymousUser()),
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
            self.source, get_request("/", user=AnonymousUser()), self.identifier, {}
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.DENY)
        flow_manager.get_flow()
        # With username
        flow_manager = OAuthSourceFlowManager(
            self.source,
            get_request("/", user=AnonymousUser()),
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
            get_request("/", user=AnonymousUser()),
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
            get_request("/", user=AnonymousUser()),
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
            get_request("/", user=AnonymousUser()),
            self.identifier,
            {"username": "foo"},
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.ENROLL)
        flow_manager.get_flow()

    def test_error_non_applicable_flow(self):
        """Test error handling when a source selected flow is non-applicable due to a policy"""
        self.source.user_matching_mode = SourceUserMatchingModes.USERNAME_LINK

        flow = create_test_flow()
        policy = ExpressionPolicy.objects.create(
            name="false", expression="""ak_message("foo");return False"""
        )
        PolicyBinding.objects.create(
            policy=policy,
            target=flow,
            order=0,
        )
        self.source.enrollment_flow = flow
        self.source.save()

        flow_manager = OAuthSourceFlowManager(
            self.source,
            get_request("/", user=AnonymousUser()),
            self.identifier,
            {"username": "foo"},
        )
        action, _ = flow_manager.get_action()
        self.assertEqual(action, Action.ENROLL)
        response = flow_manager.get_flow()
        self.assertIsInstance(response, AccessDeniedResponse)
        # pylint: disable=no-member
        self.assertEqual(response.error_message, "foo")
