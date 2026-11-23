from asyncio.exceptions import CancelledError
from sys import modules

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError
from django.db import DatabaseError, InternalError, OperationalError, ProgrammingError
from django.http.response import Http404
from dramatiq.errors import Retry
from h11 import LocalProtocolError
from psycopg.errors import Error
from rest_framework.exceptions import APIException


class TracingIgnoredException(Exception):
    """Base Class for all errors that are suppressed, and not recorded as span errors."""


ignored_classes = (
    # Inbuilt types
    KeyboardInterrupt,
    ConnectionResetError,
    OSError,
    PermissionError,
    # Django Errors
    Error,
    ImproperlyConfigured,
    DatabaseError,
    OperationalError,
    InternalError,
    ProgrammingError,
    SuspiciousOperation,
    ValidationError,
    LocalProtocolError,
    # rest_framework error
    APIException,
    # dramatiq errors
    Retry,
    # custom baseclass
    TracingIgnoredException,
    # End-user errors
    Http404,
    # AsyncIO
    CancelledError,
)


# Exceptions of optional, heavy libraries. Checked only once the library has been imported,
# as an exception can't come from a module that was never loaded.
lazy_ignored_classes = (
    ("websockets.exceptions", "WebSocketException"),
    ("ldap3.core.exceptions", "LDAPException"),
    ("docker.errors", "DockerException"),
)


def should_ignore_exception(exc: Exception) -> bool:
    """Check if an exception should be dropped"""
    if isinstance(exc, ignored_classes):
        return True
    return any(
        module in modules and isinstance(exc, getattr(modules[module], name))
        for module, name in lazy_ignored_classes
    )
