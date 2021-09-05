"""Test HTTP Helpers"""
from django.test import RequestFactory, TestCase

from authentik.core.models import USER_ATTRIBUTE_CAN_OVERRIDE_IP, Token, TokenIntents, User
from authentik.lib.utils.http import OUTPOST_REMOTE_IP_HEADER, OUTPOST_TOKEN_HEADER, get_client_ip


class TestHTTP(TestCase):
    """Test HTTP Helpers"""

    def setUp(self) -> None:
        self.user = User.objects.get(username="akadmin")
        self.factory = RequestFactory()

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
        # Invalid, non-existant token
        request = self.factory.get(
            "/",
            **{
                OUTPOST_REMOTE_IP_HEADER: "1.2.3.4",
                OUTPOST_TOKEN_HEADER: "abc",
            },
        )
        self.assertEqual(get_client_ip(request), "127.0.0.1")
        # Invalid, user doesn't have permisions
        request = self.factory.get(
            "/",
            **{
                OUTPOST_REMOTE_IP_HEADER: "1.2.3.4",
                OUTPOST_TOKEN_HEADER: token.key,
            },
        )
        self.assertEqual(get_client_ip(request), "127.0.0.1")
        # Valid
        self.user.attributes[USER_ATTRIBUTE_CAN_OVERRIDE_IP] = True
        self.user.save()
        request = self.factory.get(
            "/",
            **{
                OUTPOST_REMOTE_IP_HEADER: "1.2.3.4",
                OUTPOST_TOKEN_HEADER: token.key,
            },
        )
        self.assertEqual(get_client_ip(request), "1.2.3.4")
