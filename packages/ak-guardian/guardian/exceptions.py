"""
Exceptions used by ak-guardian. All internal and guardian-specific errors
should extend GuardianError class.
"""


class GuardianError(Exception):
    """Base class for all guardian-specific exceptions."""

    pass


class InvalidIdentity(GuardianError):
    """Raised when an object is neither User nor Group nor Role."""

    pass


class ObjectNotPersisted(GuardianError):
    """Raised when the object has not been saved to the database."""

    pass


class WrongAppError(GuardianError):
    """Raised when the app name for a permission is incorrect."""

    pass


class MixedContentTypeError(GuardianError):
    """Raised when content type for the provided permissions and/or class do not match."""

    pass


class MultipleIdentityAndObjectError(GuardianError):
    """Raised when an operation is attempted on both user/group and object."""

    pass
