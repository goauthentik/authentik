"""Plex Views"""
from urllib.parse import urlencode

from django.http.response import Http404
from requests import Session
from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from authentik import __version__
from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.sources.plex.models import PlexSource, PlexSourceConnection

LOGGER = get_logger()
SESSION_ID_KEY = "PLEX_ID"
SESSION_CODE_KEY = "PLEX_CODE"


class PlexAuth:
    """Plex authentication utilities"""

    _source: PlexSource
    _token: str

    def __init__(self, source: PlexSource, token: str):
        self._source = source
        self._token = token
        self._session = Session()
        self._session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )
        self._session.headers.update(self.headers)

    @property
    def headers(self) -> dict[str, str]:
        """Get common headers"""
        return {
            "X-Plex-Product": "authentik",
            "X-Plex-Version": __version__,
            "X-Plex-Device-Vendor": "BeryJu.org",
        }

    def get_resources(self) -> list[dict]:
        """Get all resources the plex-token has access to"""
        qs = {
            "X-Plex-Token": self._token,
            "X-Plex-Client-Identifier": self._source.client_id,
        }
        response = self._session.get(
            f"https://plex.tv/api/v2/resources?{urlencode(qs)}",
        )
        response.raise_for_status()
        return response.json()

    def get_friends(self) -> list[dict]:
        """Get plex friends"""
        qs = {
            "X-Plex-Token": self._token,
            "X-Plex-Client-Identifier": self._source.client_id,
        }
        response = self._session.get(
            f"https://plex.tv/api/v2/friends?{urlencode(qs)}",
        )
        response.raise_for_status()
        return response.json()

    def get_user_info(self) -> tuple[dict, int]:
        """Get user info of the plex token"""
        qs = {
            "X-Plex-Token": self._token,
            "X-Plex-Client-Identifier": self._source.client_id,
        }
        response = self._session.get(
            f"https://plex.tv/api/v2/user?{urlencode(qs)}",
        )
        response.raise_for_status()
        raw_user_info = response.json()
        return {
            "username": raw_user_info.get("username"),
            "email": raw_user_info.get("email"),
            "name": raw_user_info.get("title"),
        }, raw_user_info.get("id")

    def check_server_overlap(self) -> bool:
        """Check if the plex-token has any server overlap with our configured servers"""
        try:
            resources = self.get_resources()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch user resources", exc=exc)
            raise Http404
        else:
            for resource in resources:
                if resource["provides"] != "server":
                    continue
                if resource["clientIdentifier"] in self._source.allowed_servers:
                    LOGGER.info(
                        "Plex allowed access from server", name=resource["name"]
                    )
                    return True
        return False


class PlexSourceFlowManager(SourceFlowManager):
    """Flow manager for plex sources"""

    connection_type = PlexSourceConnection

    def update_connection(
        self, connection: PlexSourceConnection, plex_token: str
    ) -> PlexSourceConnection:
        """Set the access_token on the connection"""
        connection.plex_token = plex_token
        return connection
