"""Common SAML Exceptions"""

from authentik.lib.sentry import SentryIgnoredException


class CannotHandleAssertion(SentryIgnoredException):
    """This processor does not handle this assertion."""
