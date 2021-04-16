"""Plex OAuth Views"""
from typing import Any, Optional
from urllib.parse import urlencode

from django.http.response import Http404
from requests import post
from requests.api import get
from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from authentik import __version__
from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.types.manager import MANAGER, SourceType
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()
SESSION_ID_KEY = "PLEX_ID"
SESSION_CODE_KEY = "PLEX_CODE"
DEFAULT_PAYLOAD = {
    "X-Plex-Product": "authentik",
    "X-Plex-Version": __version__,
    "X-Plex-Device-Vendor": "BeryJu.org",
}


class PlexRedirect(OAuthRedirect):
    """Plex Auth redirect, get a pin then redirect to a URL to claim it"""

    headers = {}

    def get_pin(self, **data) -> dict:
        """Get plex pin that the user will claim
        https://forums.plex.tv/t/authenticating-with-plex/609370"""
        return post(
            "https://plex.tv/api/v2/pins.json?strong=true",
            data=data,
            headers=self.headers,
        ).json()

    def get_redirect_url(self, **kwargs) -> str:
        slug = kwargs.get("source_slug", "")
        self.headers = {"Origin": self.request.build_absolute_uri("/")}
        try:
            source: OAuthSource = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404(f"Unknown OAuth source '{slug}'.")
        else:
            payload = DEFAULT_PAYLOAD.copy()
            payload["X-Plex-Client-Identifier"] = source.consumer_key
            # Get a pin first
            pin = self.get_pin(**payload)
            LOGGER.debug("Got pin", **pin)
            self.request.session[SESSION_ID_KEY] = pin["id"]
            self.request.session[SESSION_CODE_KEY] = pin["code"]
            qs = {
                "clientID": source.consumer_key,
                "code": pin["code"],
                "forwardUrl": self.request.build_absolute_uri(
                    self.get_callback_url(source)
                ),
            }
            return f"https://app.plex.tv/auth#!?{urlencode(qs)}"


class PlexOAuthClient(OAuth2Client):
    """Retrive the plex token after authentication, then ask the plex API about user info"""

    def check_application_state(self) -> bool:
        return SESSION_ID_KEY in self.request.session

    def get_access_token(self, **request_kwargs) -> Optional[dict[str, Any]]:
        payload = dict(DEFAULT_PAYLOAD)
        payload["X-Plex-Client-Identifier"] = self.source.consumer_key
        payload["Accept"] = "application/json"
        response = get(
            f"https://plex.tv/api/v2/pins/{self.request.session[SESSION_ID_KEY]}",
            headers=payload,
        )
        response.raise_for_status()
        token = response.json()["authToken"]
        return {"plex_token": token}

    def get_profile_info(self, token: dict[str, str]) -> Optional[dict[str, Any]]:
        "Fetch user profile information."
        qs = {"X-Plex-Token": token["plex_token"]}
        try:
            response = self.do_request(
                "get", f"https://plex.tv/users/account.json?{urlencode(qs)}"
            )
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch user profile", exc=exc)
            return None
        else:
            return response.json().get("user", {})


class PlexOAuth2Callback(OAuthCallback):
    """Plex OAuth2 Callback"""

    client_class = PlexOAuthClient

    def get_user_id(
        self, source: UserOAuthSourceConnection, info: dict[str, Any]
    ) -> Optional[str]:
        return info.get("uuid")

    def get_user_enroll_context(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("username"),
            "email": info.get("email"),
            "name": info.get("title"),
        }


@MANAGER.type()
class PlexType(SourceType):
    """Plex Type definition"""

    redirect_view = PlexRedirect
    callback_view = PlexOAuth2Callback
    name = "Plex"
    slug = "plex"

    authorization_url = ""
    access_token_url = ""  # nosec
    profile_url = ""
