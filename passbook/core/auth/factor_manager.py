"""Authentication Factor Manager"""
from logging import getLogger

LOGGER = getLogger(__name__)

class AuthenticationFactorManager:
    """Manager to hold all Factors."""

    __factors = []

    def factor(self):
        """Class decorator to register classes inline."""
        def inner_wrapper(cls):
            self.__factors.append(cls)
            LOGGER.debug("Registered factor '%s'", cls.__name__)
            return cls
        return inner_wrapper

    @property
    def all(self):
        """Get list of all registered factors"""
        return self.__factors


MANAGER = AuthenticationFactorManager()
