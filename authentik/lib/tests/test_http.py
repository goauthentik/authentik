"""Test HTTP Helpers"""
from django.test import RequestFactory, TestCase

from authentik.core.models import Token, TokenIntents, UserTypes
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.utils.http import OUTPOST_REMOTE_IP_HEADER, OUTPOST_TOKEN_HEADER, get_client_ip
from authentik.lib.views import bad_request_message


class TestHTTP(TestCase):
    """Test HTTP Helpers"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.factory = RequestFactory()

    def test_bad_request_message(self):
        """test bad_request_message"""
        request = self.factory.get("/")
        self.assertEqual(bad_request_message(request, "foo").status_code, 400)

    def test_normal(self):
        """Test normal request"""
        request = self.factory.get("/")
        self.assertEqual(get_client_ip(request), "127.0.0.1")

    def test_forward_for(self):
        """Test x-forwarded-for request"""
        request = self.factory.get("/", HTTP_X_FORWARDED_FOR="127.0.0.2")
        self.assertEqual(get_client_ip(request), "127.0.0.2")

    def test_fake_outpost(self):
        """Test faked IP which is overridden by an outpost"""
        token = Token.objects.create(
            identifier="test", user=self.user, intent=TokenIntents.INTENT_API
        )
        # Invalid, non-existent token
        request = self.factory.get(
            "/",
            **{
                OUTPOST_REMOTE_IP_HEADER: "1.2.3.4",
                OUTPOST_TOKEN_HEADER: "abc",
            },
        )
        self.assertEqual(get_client_ip(request), "127.0.0.1")
        # Invalid, user doesn't have permissions
        request = self.factory.get(
            "/",
            **{
                OUTPOST_REMOTE_IP_HEADER: "1.2.3.4",
                OUTPOST_TOKEN_HEADER: token.key,
            },
        )
        self.assertEqual(get_client_ip(request), "127.0.0.1")
        # Valid
        self.user.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        self.user.save()
        request = self.factory.get(
            "/",
            **{
                OUTPOST_REMOTE_IP_HEADER: "1.2.3.4",
                OUTPOST_TOKEN_HEADER: token.key,
            },
        )
        self.assertEqual(get_client_ip(request), "1.2.3.4")
