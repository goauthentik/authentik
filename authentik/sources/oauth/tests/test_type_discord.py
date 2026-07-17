"""Discord Type tests"""

from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase
from requests_mock import Mocker

from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.discord import DiscordOAuth2Callback, DiscordType

# https://discord.com/developers/docs/resources/user#user-object
DISCORD_USER = {
    "id": "80351110224678912",
    "username": "Nelly",
    "discriminator": "1337",
    "avatar": "8342729096ea3675442027381ff50dfe",
    "verified": True,
    "email": "nelly@discord.com",
    "flags": 64,
    "premium_type": 1,
    "public_flags": 64,
}

DISCORD_USER_NO_AVATAR = {**DISCORD_USER, "avatar": None}
DISCORD_USER_GLOBAL_NAME = {**DISCORD_USER, "global_name": "Nelly Global"}

GUILD_ID = "1234567890"

DISCORD_GUILD_MEMBER = {
    "roles": ["111111111111111111", "222222222222222222"],
    "nick": "Nelly Guild",
    "joined_at": "2021-01-01T00:00:00.000Z",
    "user": DISCORD_USER,
}

TOKEN_WITHOUT_GUILD_SCOPE = {
    "access_token": generate_id(),
    "token_type": "Bearer",
    "scope": "email identify",
}

TOKEN_WITH_GUILD_SCOPE = {
    "access_token": generate_id(),
    "token_type": "Bearer",
    "scope": "email identify guilds.members.read",
}


class TestTypeDiscord(TestCase):
    """Discord OAuth Source type tests"""

    def setUp(self):
        self.factory = RequestFactory()
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="discord",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    def test_enroll_context(self):
        """Test discord Enrollment context"""
        ak_context = DiscordType().get_base_user_properties(
            source=self.source, info=DISCORD_USER, client=None, token=TOKEN_WITHOUT_GUILD_SCOPE
        )
        self.assertEqual(ak_context["username"], DISCORD_USER["username"])
        self.assertEqual(ak_context["email"], DISCORD_USER["email"])
        self.assertEqual(ak_context["name"], DISCORD_USER["username"])
        self.assertEqual(ak_context["groups"], [])

    def test_avatar_url_with_avatar(self):
        """Avatar URL is set when user has an avatar"""
        ak_context = DiscordType().get_base_user_properties(
            source=self.source, info=DISCORD_USER, client=None, token=TOKEN_WITHOUT_GUILD_SCOPE
        )
        expected = (
            f"https://cdn.discordapp.com/avatars/{DISCORD_USER['id']}"
            f"/{DISCORD_USER['avatar']}.png?size=64"
        )
        self.assertEqual(ak_context["attributes"]["discord_avatar"], expected)

    def test_avatar_url_without_avatar(self):
        """Avatar URL is None when user has no avatar"""
        ak_context = DiscordType().get_base_user_properties(
            source=self.source,
            info=DISCORD_USER_NO_AVATAR,
            client=None,
            token=TOKEN_WITHOUT_GUILD_SCOPE,
        )
        self.assertIsNone(ak_context["attributes"]["discord_avatar"])

    def test_role_sync_returns_roles(self):
        """Role IDs are synced when guild_id is set and guilds.members.read scope is present"""
        self.source.discord_guild_id = GUILD_ID
        self.source.save()

        with Mocker() as mocker:
            mocker.get(
                f"https://discord.com/api/v10/users/@me/guilds/{GUILD_ID}/member",
                json=DISCORD_GUILD_MEMBER,
            )
            token = TOKEN_WITH_GUILD_SCOPE
            callback = DiscordOAuth2Callback(
                source=self.source,
                request=self.factory.get("/"),
                token=token,
            )
            ak_context = DiscordType().get_base_user_properties(
                source=self.source,
                info=DISCORD_USER,
                client=callback.get_client(self.source),
                token=token,
            )

        self.assertEqual(ak_context["groups"], DISCORD_GUILD_MEMBER["roles"])

    def test_role_sync_skipped_without_scope(self):
        """Role sync is skipped when guilds.members.read scope is absent, even if guild_id is set"""
        self.source.discord_guild_id = GUILD_ID
        self.source.save()

        ak_context = DiscordType().get_base_user_properties(
            source=self.source,
            info=DISCORD_USER,
            client=None,
            token=TOKEN_WITHOUT_GUILD_SCOPE,
        )
        self.assertEqual(ak_context["groups"], [])

    def test_role_sync_skipped_without_guild_id(self):
        """Role sync is skipped when no guild_id is configured"""
        mock_client = MagicMock()

        ak_context = DiscordType().get_base_user_properties(
            source=self.source,
            info=DISCORD_USER,
            client=mock_client,
            token=TOKEN_WITH_GUILD_SCOPE,
        )
        self.assertEqual(ak_context["groups"], [])
        mock_client.get_guild_member.assert_not_called()

    def test_guild_sync_member_has_no_roles(self):
        """Groups are empty when the member has no roles"""
        self.source.discord_guild_id = GUILD_ID
        self.source.save()

        with Mocker() as mocker:
            mocker.get(
                f"https://discord.com/api/v10/users/@me/guilds/{GUILD_ID}/member",
                json={"roles": [], "nick": None, "joined_at": "2021-01-01T00:00:00.000Z"},
            )
            token = TOKEN_WITH_GUILD_SCOPE
            callback = DiscordOAuth2Callback(
                source=self.source,
                request=self.factory.get("/"),
                token=token,
            )
            ak_context = DiscordType().get_base_user_properties(
                source=self.source,
                info=DISCORD_USER,
                client=callback.get_client(self.source),
                token=token,
            )

        self.assertEqual(ak_context["groups"], [])
