"""Source type manager"""
from enum import Enum
from typing import Callable, Dict, List

from django.utils.text import slugify
from structlog import get_logger

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()


class RequestKind(Enum):
    """Enum of OAuth Request types"""

    callback = "callback"
    redirect = "redirect"


class SourceTypeManager:
    """Manager to hold all Source types."""

    __source_types: Dict[RequestKind, Dict[str, Callable]] = {}
    __names: List[str] = []

    def source(self, kind: RequestKind, name: str):
        """Class decorator to register classes inline."""

        def inner_wrapper(cls):
            if kind.value not in self.__source_types:
                self.__source_types[kind.value] = {}
            self.__source_types[kind.value][slugify(name)] = cls
            self.__names.append(name)
            return cls

        return inner_wrapper

    def get_name_tuple(self):
        """Get list of tuples of all registered names"""
        return [(slugify(x), x) for x in set(self.__names)]

    def find(self, source: OAuthSource, kind: RequestKind) -> Callable:
        """Find fitting Source Type"""
        if kind.value in self.__source_types:
            if source.provider_type in self.__source_types[kind.value]:
                return self.__source_types[kind.value][source.provider_type]
            LOGGER.warning(
                "no matching type found, using default",
                wanted=source.provider_type,
                have=self.__source_types[kind.value].keys(),
            )
            # Return defaults
            if kind == RequestKind.callback:
                return OAuthCallback
            if kind == RequestKind.redirect:
                return OAuthRedirect
        raise KeyError(
            f"Provider Type {source.provider_type} (type {kind.value}) not found."
        )


MANAGER = SourceTypeManager()
