"""TikTok Type tests"""

from django.test import RequestFactory, TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.tiktok import TikTokType

# https://developers.tiktok.com/doc/tiktok-api-v2-get-user-info
TIKTOK_USER = {
    "open_id": "723f24d7-e717-40f8-a2b6-cb8464cd23b4",
    "union_id": "c9c60f44-a68e-4f5d-84dd-ce22faf4e0c7",
    "display_name": "Tik Toker",
    "avatar_url": "https://p16-sign-sg.tiktokcdn.com/aweme/100x100/tos-alisg-avt-0068/example.jpeg",
}


class TestTypeTikTok(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="tiktok",
        )
        self.factory = RequestFactory()

    def test_enroll_context(self):
        """Test TikTok Enrollment context"""
        ak_context = TikTokType().get_base_user_properties(
            source=self.source, info=TIKTOK_USER, client=None, token={}
        )
        self.assertEqual(ak_context["username"], TIKTOK_USER["union_id"])
        self.assertIsNone(ak_context["email"])
        self.assertEqual(ak_context["name"], TIKTOK_USER["display_name"])
        self.assertEqual(ak_context["attributes"]["open_id"], TIKTOK_USER["open_id"])
        self.assertEqual(ak_context["attributes"]["union_id"], TIKTOK_USER["union_id"])

    def test_enroll_context_no_union_id(self):
        """Test TikTok Enrollment context without union_id"""
        user = TIKTOK_USER.copy()
        del user["union_id"]
        ak_context = TikTokType().get_base_user_properties(
            source=self.source, info=user, client=None, token={}
        )
        self.assertEqual(ak_context["username"], TIKTOK_USER["open_id"])
        self.assertIsNone(ak_context["email"])
        self.assertEqual(ak_context["name"], TIKTOK_USER["display_name"])
