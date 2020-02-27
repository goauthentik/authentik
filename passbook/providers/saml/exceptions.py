"""passbook SAML IDP Exceptions"""
from passbook.lib.sentry import SentryIgnoredException


class CannotHandleAssertion(SentryIgnoredException):
    """This processor does not handle this assertion."""
