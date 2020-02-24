"""logging helpers"""
from os import getpid


# pylint: disable=unused-argument
def add_process_id(logger, method_name, event_dict):
    """Add the current process ID"""
    event_dict["pdi"] = getpid()
    return event_dict
