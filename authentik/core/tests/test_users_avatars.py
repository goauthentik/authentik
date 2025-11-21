"""Test Users Avatars"""

from json import loads

from django.core.cache import cache
from django.urls.base import reverse
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.tenants.utils import get_current_tenant


class TestUsersAvatars(APITestCase):
    """Test Users avatars"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = User.objects.create(username="test-user")

    def set_avatar_mode(self, mode: str):
        """Set the avatar mode on the current tenant."""
        tenant = get_current_tenant()
        tenant.avatars = mode
        tenant.save()

    def test_avatars_none(self):
        """Test avatars none"""
        self.set_avatar_mode("none")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["user"]["avatar"], "/static/dist/assets/images/user_default.png")

    def test_avatars_gravatar(self):
        """Test avatars gravatar"""
        self.set_avatar_mode("gravatar")
        self.admin.email = "static@t.goauthentik.io"
        self.admin.save()
        self.client.force_login(self.admin)
        with Mocker() as mocker:
            mocker.head(
                (
                    "https://www.gravatar.com/avatar/76eb3c74c8beb6faa037f1b6e2ecb3e252bdac"
                    "6cf71fb567ae36025a9d4ea86b?size=158&rating=g&default=404"
                ),
                text="foo",
                headers={"Content-Type": "image/png"},
            )
            response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("gravatar", body["user"]["avatar"])

    def test_avatars_initials(self):
        """Test avatars initials"""
        self.set_avatar_mode("initials")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])

    def test_avatars_custom(self):
        """Test avatars custom"""
        self.set_avatar_mode("foo://%(username)s")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["user"]["avatar"], f"foo://{self.admin.username}")

    def test_avatars_attributes(self):
        """Test avatars attributes"""
        self.set_avatar_mode("attributes.foo.avatar")
        self.admin.attributes = {"foo": {"avatar": "bar"}}
        self.admin.save()
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["user"]["avatar"], "bar")

    def test_avatars_fallback(self):
        """Test fallback"""
        self.set_avatar_mode("attributes.foo.avatar,initials")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])

    def test_avatars_custom_content_type_valid(self):
        """Test custom avatar URL with valid image Content-Type"""
        cache.clear()
        self.set_avatar_mode("https://example.com/avatar/%(username)s")
        self.client.force_login(self.admin)
        with Mocker() as mocker:
            mocker.head(
                f"https://example.com/avatar/{self.admin.username}",
                headers={"Content-Type": "image/png"},
            )
            response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(
            body["user"]["avatar"], f"https://example.com/avatar/{self.admin.username}"
        )

    def test_avatars_custom_content_type_invalid(self):
        """Test custom avatar URL with invalid Content-Type falls back"""
        cache.clear()
        self.set_avatar_mode("https://example.com/avatar/%(username)s,initials")
        self.client.force_login(self.admin)
        with Mocker() as mocker:
            mocker.head(
                f"https://example.com/avatar/{self.admin.username}",
                headers={"Content-Type": "text/html"},
            )
            response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        # Should fallback to initials since Content-Type is not image/*
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])

    def test_avatars_custom_content_type_missing(self):
        """Test custom avatar URL with missing Content-Type header falls back"""
        cache.clear()
        self.set_avatar_mode("https://example.com/avatar/%(username)s,initials")
        self.client.force_login(self.admin)
        with Mocker() as mocker:
            mocker.head(
                f"https://example.com/avatar/{self.admin.username}",
                headers={},
            )
            response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        # Should fallback to initials since Content-Type header is missing
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])

    def test_avatars_custom_404_cached(self):
        """Test that 404 responses are cached with TTL"""
        cache.clear()
        self.set_avatar_mode("https://example.com/avatar/%(username)s")
        self.client.force_login(self.admin)
        with Mocker() as mocker:
            mocker.head(
                f"https://example.com/avatar/{self.admin.username}",
                status_code=404,
            )
            response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        # Should fallback to default avatar
        self.assertEqual(body["user"]["avatar"], "/static/dist/assets/images/user_default.png")

        # Verify cache was set with the expected structure
        from hashlib import md5

        mail_hash = md5(self.admin.email.lower().encode("utf-8"), usedforsecurity=False).hexdigest()
        cache_key = f"goauthentik.io/lib/avatars/example.com/{mail_hash}"
        self.assertIsNone(cache.get(cache_key))
        # Verify TTL was set (cache entry exists)
        self.assertTrue(cache.has_key(cache_key))

    def test_avatars_custom_redirect(self):
        """Test custom avatar URL follows redirects"""
        cache.clear()
        self.set_avatar_mode("https://example.com/avatar/%(username)s")
        self.client.force_login(self.admin)
        with Mocker() as mocker:
            # Mock a redirect
            mocker.head(
                f"https://example.com/avatar/{self.admin.username}",
                status_code=302,
                headers={"Location": "https://cdn.example.com/final-avatar.png"},
            )
            mocker.head(
                "https://cdn.example.com/final-avatar.png",
                headers={"Content-Type": "image/png"},
            )
            response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        # Should return the original URL (not the redirect destination)
        self.assertEqual(
            body["user"]["avatar"], f"https://example.com/avatar/{self.admin.username}"
        )

    def test_avatars_hostname_availability_cache(self):
        """Test that hostname availability is cached when domain fails"""
        from requests.exceptions import Timeout

        cache.clear()
        self.set_avatar_mode("https://failing.example.com/avatar/%(username)s,initials")
        self.client.force_login(self.admin)

        with Mocker() as mocker:
            # First request times out
            mocker.head(
                f"https://failing.example.com/avatar/{self.admin.username}",
                exc=Timeout("Connection timeout"),
            )
            response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        # Should fallback to initials
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])

        # Verify hostname is marked as unavailable
        cache_key_hostname = "goauthentik.io/lib/avatars/failing.example.com/available"
        self.assertFalse(cache.get(cache_key_hostname, True))

        # Second request should not even try to fetch (hostname cached as unavailable)
        with Mocker() as mocker:
            # This should NOT be called due to hostname cache
            mocker.head(
                f"https://failing.example.com/avatar/{self.admin.username}",
                headers={"Content-Type": "image/png"},
            )
            response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        # Should still fallback to initials without making a request
        self.assertIn("data:image/svg+xml;base64,", body["user"]["avatar"])
        # Verify no request was made (request_history should be empty)
        self.assertEqual(len(mocker.request_history), 0)

    def test_avatars_gravatar_uses_url_validation(self):
        """Test that Gravatar now uses avatar_mode_url validation (regression test)"""
        cache.clear()
        self.set_avatar_mode("gravatar")
        self.admin.email = "test@example.com"
        self.admin.save()
        self.client.force_login(self.admin)

        with Mocker() as mocker:
            # Mock Gravatar to return non-image content
            from hashlib import sha256

            mail_hash = sha256(self.admin.email.lower().encode("utf-8")).hexdigest()
            gravatar_url = (
                f"https://www.gravatar.com/avatar/{mail_hash}?size=158&rating=g&default=404"
            )

            mocker.head(
                gravatar_url,
                headers={"Content-Type": "text/html"},
            )
            response = self.client.get(reverse("authentik_api:user-me"))

        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        # Should fallback to default avatar since Content-Type is not image/*
        self.assertEqual(body["user"]["avatar"], "/static/dist/assets/images/user_default.png")
