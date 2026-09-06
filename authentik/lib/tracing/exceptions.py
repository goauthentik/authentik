from asyncio.exceptions import CancelledError

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError
from django.db import DatabaseError, InternalError, OperationalError, ProgrammingError
from django.http.response import Http404
from docker.errors import DockerException
from dramatiq.errors import Retry
from h11 import LocalProtocolError
from ldap3.core.exceptions import LDAPException
from psycopg.errors import Error
from rest_framework.exceptions import APIException
from websockets.exceptions import WebSocketException


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
    # websocket errors
    WebSocketException,
    LocalProtocolError,
    # rest_framework error
    APIException,
    # dramatiq errors
    Retry,
    # custom baseclass
    TracingIgnoredException,
    # ldap errors
    LDAPException,
    # Docker errors
    DockerException,
    # End-user errors
    Http404,
    # AsyncIO
    CancelledError,
)


def should_ignore_exception(exc: Exception) -> bool:
    """Check if an exception should be dropped"""
    return isinstance(exc, ignored_classes)
