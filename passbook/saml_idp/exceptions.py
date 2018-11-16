"""passbook SAML IDP Exceptions"""


class CannotHandleAssertion(Exception):
    """This processor does not handle this assertion."""
    pass


class UserNotAuthorized(Exception):
    """User not authorized for SAML 2.0 authentication."""
    pass
