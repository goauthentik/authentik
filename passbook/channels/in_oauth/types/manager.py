"""Inlet type manager"""
from enum import Enum

from django.utils.text import slugify
from structlog import get_logger

from passbook.channels.in_oauth.views.core import OAuthCallback, OAuthRedirect

LOGGER = get_logger()


class RequestKind(Enum):
    """Enum of OAuth Request types"""

    callback = "callback"
    redirect = "redirect"


class InletTypeManager:
    """Manager to hold all Inlet types."""

    __inlet_types = {}
    __names = []

    def inlet(self, kind, name):
        """Class decorator to register classes inline."""

        def inner_wrapper(cls):
            if kind not in self.__inlet_types:
                self.__inlet_types[kind] = {}
            self.__inlet_types[kind][name.lower()] = cls
            self.__names.append(name)
            LOGGER.debug("Registered inlet", inlet_class=cls.__name__, kind=kind)
            return cls

        return inner_wrapper

    def get_name_tuple(self):
        """Get list of tuples of all registered names"""
        return [(slugify(x), x) for x in set(self.__names)]

    def find(self, inlet, kind):
        """Find fitting Inlet Type"""
        if kind in self.__inlet_types:
            if inlet.provider_type in self.__inlet_types[kind]:
                return self.__inlet_types[kind][inlet.provider_type]
            # Return defaults
            if kind == RequestKind.callback:
                return OAuthCallback
            if kind == RequestKind.redirect:
                return OAuthRedirect
        raise KeyError


MANAGER = InletTypeManager()
