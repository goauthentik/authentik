"""Source type manager"""
from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional

from structlog.stdlib import get_logger

from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()

if TYPE_CHECKING:
    from authentik.sources.oauth.models import OAuthSource


class RequestKind(Enum):
    """Enum of OAuth Request types"""

    CALLBACK = "callback"
    REDIRECT = "redirect"


class SourceType:
    """Source type, allows overriding of urls and views per type"""

    callback_view = OAuthCallback
    redirect_view = OAuthRedirect
    name: str
    slug: str

    urls_customizable = False

    request_token_url: Optional[str] = None
    authorization_url: Optional[str] = None
    access_token_url: Optional[str] = None
    profile_url: Optional[str] = None


class SourceTypeManager:
    """Manager to hold all Source types."""

    __sources: list[SourceType] = []

    def type(self):
        """Class decorator to register classes inline."""

        def inner_wrapper(cls):
            self.__sources.append(cls)
            return cls

        return inner_wrapper

    def get(self):
        """Get a list of all source types"""
        return self.__sources

    def get_name_tuple(self):
        """Get list of tuples of all registered names"""
        return [(x.slug, x.name) for x in self.__sources]

    def find_type(self, type_name: str) -> SourceType:
        """Find type based on source"""
        found_type = None
        for src_type in self.__sources:
            if src_type.slug == type_name:
                return src_type
        if not found_type:
            found_type = SourceType()
            LOGGER.warning(
                "no matching type found, using default",
                wanted=type_name,
                have=[x.name for x in self.__sources],
            )
        return found_type

    def find(self, source: "OAuthSource", kind: RequestKind) -> Callable:
        """Find fitting Source Type"""
        found_type = self.find_type(source)
        if kind == RequestKind.CALLBACK:
            return found_type.callback_view
        if kind == RequestKind.REDIRECT:
            return found_type.redirect_view
        raise ValueError


MANAGER = SourceTypeManager()
