"""passbook SAML IDP Exceptions"""


class CannotHandleAssertion(Exception):
    """This processor does not handle this assertion."""


class UserNotAuthorized(Exception):
    """User not authorized for SAML 2.0 authentication."""
