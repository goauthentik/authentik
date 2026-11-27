"""Plex Views"""

from urllib.parse import urlencode

from django.http.response import Http404
from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from authentik import authentik_version
from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.lib.utils.http import get_http_session
from authentik.sources.plex.models import (
    GroupPlexSourceConnection,
    PlexSource,
    UserPlexSourceConnection,
)

LOGGER = get_logger()


class PlexAuth:
    """Plex authentication utilities"""

    _source: PlexSource
    _token: str

    def __init__(self, source: PlexSource, token: str):
        self._source = source
        self._token = token
        self._session = get_http_session()
        self._session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )
        self._session.headers.update(self.headers)

    @property
    def headers(self) -> dict[str, str]:
        """Get common headers"""
        return {
            "X-Plex-Product": "authentik",
            "X-Plex-Version": authentik_version(),
            "X-Plex-Device-Vendor": "goauthentik.io",
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
        return raw_user_info, raw_user_info.get("id")

    def check_server_overlap(self) -> bool:
        """Check if the plex-token has any server overlap with our configured servers"""
        try:
            resources = self.get_resources()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch user resources", exc=exc)
            raise Http404 from None
        for resource in resources:
            if resource["provides"] != "server":
                continue
            if resource["clientIdentifier"] in self._source.allowed_servers:
                LOGGER.info("Plex allowed access from server", name=resource["name"])
                return True
        return False

    def check_friends_overlap(self, user_ident: int) -> bool:
        """Check if the user is a friend of the owner, or the owner themselves"""
        _, owner_id = self.get_user_info()
        if owner_id == user_ident:
            return True
        try:
            owner_friends = self.get_friends()
        except RequestException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            LOGGER.warning(
                "Unable to fetch Plex friends",
                exc_type=type(exc).__name__,
                status_code=status_code,
            )
            return False
        for friend in owner_friends:
            if int(friend.get("id", "0")) == user_ident:
                LOGGER.info(
                    "allowing user for plex because of friend",
                    user=user_ident,
                )
                return True
        return False


class PlexSourceFlowManager(SourceFlowManager):
    """Flow manager for plex sources"""

    user_connection_type = UserPlexSourceConnection
    group_connection_type = GroupPlexSourceConnection

    def update_user_connection(
        self, connection: UserPlexSourceConnection, **kwargs
    ) -> UserPlexSourceConnection:
        """Set the access_token on the connection"""
        connection.plex_token = kwargs.get("plex_token")
        return connection
