"""Twitter Type tests"""
from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.twitter import TwitterOAuthCallback

# https://developer.twitter.com/en/docs/twitter-api/v1/accounts-and-users/manage-account-settings/ \
# api-reference/get-account-verify_credentials
TWITTER_USER = {
    "contributors_enabled": True,
    "created_at": "Sat May 09 17:58:22 +0000 2009",
    "default_profile": False,
    "default_profile_image": False,
    "description": "I taught your phone that thing you like.",
    "favourites_count": 588,
    "follow_request_sent": None,
    "followers_count": 10625,
    "following": None,
    "friends_count": 1181,
    "geo_enabled": True,
    "id": 38895958,
    "id_str": "38895958",
    "is_translator": False,
    "lang": "en",
    "listed_count": 190,
    "location": "San Francisco",
    "name": "Sean Cook",
    "notifications": None,
    "profile_background_color": "1A1B1F",
    "profile_background_image_url": "",
    "profile_background_image_url_https": "",
    "profile_background_tile": True,
    "profile_image_url": "",
    "profile_image_url_https": "",
    "profile_link_color": "2FC2EF",
    "profile_sidebar_border_color": "181A1E",
    "profile_sidebar_fill_color": "252429",
    "profile_text_color": "666666",
    "profile_use_background_image": True,
    "protected": False,
    "screen_name": "theSeanCook",
    "show_all_inline_media": True,
    "status": {
        "contributors": None,
        "coordinates": {"coordinates": [-122.45037293, 37.76484123], "type": "Point"},
        "created_at": "Tue Aug 28 05:44:24 +0000 2012",
        "favorited": False,
        "geo": {"coordinates": [37.76484123, -122.45037293], "type": "Point"},
        "id": 240323931419062272,
        "id_str": "240323931419062272",
        "in_reply_to_screen_name": "messl",
        "in_reply_to_status_id": 240316959173009410,
        "in_reply_to_status_id_str": "240316959173009410",
        "in_reply_to_user_id": 18707866,
        "in_reply_to_user_id_str": "18707866",
        "place": {
            "attributes": {},
            "bounding_box": {
                "coordinates": [
                    [
                        [-122.45778216, 37.75932999],
                        [-122.44248216, 37.75932999],
                        [-122.44248216, 37.76752899],
                        [-122.45778216, 37.76752899],
                    ]
                ],
                "type": "Polygon",
            },
            "country": "United States",
            "country_code": "US",
            "full_name": "Ashbury Heights, San Francisco",
            "id": "866269c983527d5a",
            "name": "Ashbury Heights",
            "place_type": "neighborhood",
            "url": "http://api.twitter.com/1/geo/id/866269c983527d5a.json",
        },
        "retweet_count": 0,
        "retweeted": False,
        "source": "Twitter for  iPhone",
        "text": "@messl congrats! So happy for all 3 of you.",
        "truncated": False,
    },
    "statuses_count": 2609,
    "time_zone": "Pacific Time (US & Canada)",
    "url": None,
    "utc_offset": -28800,
    "verified": False,
}


class TestTypeGitHub(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openidconnect",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    def test_enroll_context(self):
        """Test Twitter Enrollment context"""
        ak_context = TwitterOAuthCallback().get_user_enroll_context(TWITTER_USER)
        self.assertEqual(ak_context["username"], TWITTER_USER["screen_name"])
        self.assertEqual(ak_context["email"], TWITTER_USER.get("email", None))
        self.assertEqual(ak_context["name"], TWITTER_USER["name"])
