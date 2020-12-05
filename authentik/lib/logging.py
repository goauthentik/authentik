"""logging helpers"""
from logging import Logger
from os import getpid
from typing import Callable


# pylint: disable=unused-argument
def add_process_id(logger: Logger, method_name: str, event_dict):
    """Add the current process ID"""
    event_dict["pid"] = getpid()
    return event_dict


def add_common_fields(environment: str) -> Callable:
    """Add a common field to easily search for authentik logs"""

    def add_common_field(logger: Logger, method_name: str, event_dict):
        """Add a common field to easily search for authentik logs"""
        event_dict["app"] = "authentik"
        event_dict["app_environment"] = environment
        return event_dict

    return add_common_field
