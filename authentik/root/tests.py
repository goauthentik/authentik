"""root tests"""

from pathlib import Path
from secrets import token_urlsafe
from tempfile import gettempdir

from django.test import TestCase
from django.urls import reverse

from authentik.core.models import Token, TokenIntents, UserTypes
from authentik.root.middleware import ClientIPMiddleware


class TestRoot(TestCase):
    """Test root application"""

    def setUp(self):
        _tmp = Path(gettempdir())
        self.token = token_urlsafe(32)
        with open(_tmp / "authentik-core-metrics.key", "w") as _f:
            _f.write(self.token)

    def tearDown(self):
        _tmp = Path(gettempdir())
        (_tmp / "authentik-core-metrics.key").unlink()

    def test_monitoring_error(self):
        """Test monitoring without any credentials"""
        response = self.client.get(reverse("metrics"))
        self.assertEqual(response.status_code, 401)

    def test_monitoring_ok(self):
        """Test monitoring with credentials"""
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        response = self.client.get(reverse("metrics"), **auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_monitoring_live(self):
        """Test LiveView"""
        self.assertEqual(self.client.get(reverse("health-live")).status_code, 200)

    def test_monitoring_ready(self):
        """Test ReadyView"""
        self.assertEqual(self.client.get(reverse("health-ready")).status_code, 200)

    def test_normal(self):
        """Test normal request"""
        request = self.factory.get("/")
        self.assertEqual(ClientIPMiddleware.get_client_ip(request), "127.0.0.1")

    def test_forward_for(self):
        """Test x-forwarded-for request"""
        request = self.factory.get("/", HTTP_X_FORWARDED_FOR="127.0.0.2")
        self.assertEqual(ClientIPMiddleware.get_client_ip(request), "127.0.0.2")

    def test_forward_for_invalid(self):
        """Test invalid forward for"""
        request = self.factory.get("/", HTTP_X_FORWARDED_FOR="foobar")
        self.assertEqual(ClientIPMiddleware.get_client_ip(request), ClientIPMiddleware.default_ip)

    def test_fake_outpost(self):
        """Test faked IP which is overridden by an outpost"""
        token = Token.objects.create(
            identifier="test", user=self.user, intent=TokenIntents.INTENT_API
        )
        # Invalid, non-existent token
        request = self.factory.get(
            "/",
            **{
                ClientIPMiddleware.outpost_remote_ip_header: "1.2.3.4",
                ClientIPMiddleware.outpost_token_header: "abc",
            },
        )
        self.assertEqual(ClientIPMiddleware.get_client_ip(request), "127.0.0.1")
        # Invalid, user doesn't have permissions
        request = self.factory.get(
            "/",
            **{
                ClientIPMiddleware.outpost_remote_ip_header: "1.2.3.4",
                ClientIPMiddleware.outpost_token_header: token.key,
            },
        )
        self.assertEqual(ClientIPMiddleware.get_client_ip(request), "127.0.0.1")
        # Invalid, not a real IP
        self.user.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        self.user.save()
        request = self.factory.get(
            "/",
            **{
                ClientIPMiddleware.outpost_remote_ip_header: "foobar",
                ClientIPMiddleware.outpost_token_header: token.key,
            },
        )
        self.assertEqual(ClientIPMiddleware.get_client_ip(request), "127.0.0.1")
        # Valid
        self.user.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        self.user.save()
        request = self.factory.get(
            "/",
            **{
                ClientIPMiddleware.outpost_remote_ip_header: "1.2.3.4",
                ClientIPMiddleware.outpost_token_header: token.key,
            },
        )
        self.assertEqual(ClientIPMiddleware.get_client_ip(request), "1.2.3.4")
