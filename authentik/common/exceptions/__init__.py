class AuthentikException(Exception):
    """Base class for authentik exceptions"""


class NotReportedException(AuthentikException):
    """Exception base class for all errors that are suppressed,
    and not sent to any kind of monitoring."""
