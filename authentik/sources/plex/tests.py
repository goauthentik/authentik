"""plex Source tests"""
from django.test import TestCase
from requests.exceptions import RequestException
from requests_mock import Mocker

from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_key
from authentik.sources.plex.models import PlexSource
from authentik.sources.plex.plex import PlexAuth
from authentik.sources.plex.tasks import check_plex_token_all

USER_INFO_RESPONSE = {
    "id": 1234123419,
    "uuid": "qwerqewrqewrqwr",
    "username": "username",
    "title": "title",
    "email": "foo@bar.baz",
}
RESOURCES_RESPONSE = [
    {
        "name": "foo",
        "clientIdentifier": "allowed",
        "provides": "server",
    },
    {
        "name": "foo",
        "clientIdentifier": "denied",
        "provides": "server",
    },
]


class TestPlexSource(TestCase):
    """plex Source tests"""

    def setUp(self):
        self.source: PlexSource = PlexSource.objects.create(
            name="test",
            slug="test",
        )

    def test_get_user_info(self):
        """Test get_user_info"""
        token = generate_key()
        api = PlexAuth(self.source, token)
        with Mocker() as mocker:
            mocker.get("https://plex.tv/api/v2/user", json=USER_INFO_RESPONSE)
            self.assertEqual(
                api.get_user_info(),
                (
                    {"username": "username", "email": "foo@bar.baz", "name": "title"},
                    1234123419,
                ),
            )

    def test_check_server_overlap(self):
        """Test check_server_overlap"""
        token = generate_key()
        api = PlexAuth(self.source, token)
        with Mocker() as mocker:
            mocker.get("https://plex.tv/api/v2/resources", json=RESOURCES_RESPONSE)
            self.assertFalse(api.check_server_overlap())
        self.source.allowed_servers = ["allowed"]
        self.source.save()
        with Mocker() as mocker:
            mocker.get("https://plex.tv/api/v2/resources", json=RESOURCES_RESPONSE)
            self.assertTrue(api.check_server_overlap())

    def test_check_task(self):
        """Test token check task"""
        with Mocker() as mocker:
            mocker.get("https://plex.tv/api/v2/user", json=USER_INFO_RESPONSE)
            check_plex_token_all()
            self.assertFalse(Event.objects.filter(action=EventAction.CONFIGURATION_ERROR).exists())
        with Mocker() as mocker:
            mocker.get("https://plex.tv/api/v2/user", exc=RequestException())
            check_plex_token_all()
            self.assertTrue(Event.objects.filter(action=EventAction.CONFIGURATION_ERROR).exists())
