"""logging helpers"""
from logging import Logger
from os import getpid


def add_process_id(logger: Logger, method_name: str, event_dict):
    """Add the current process ID"""
    event_dict["pid"] = getpid()
    return event_dict
