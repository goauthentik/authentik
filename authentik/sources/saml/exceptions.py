"""authentik saml source exceptions"""
from authentik.lib.sentry import SentryIgnoredException


class MissingSAMLResponse(SentryIgnoredException):
    """Exception raised when request does not contain SAML Response."""


class UnsupportedNameIDFormat(SentryIgnoredException):
    """Exception raised when SAML Response contains NameID Format not supported."""


class MismatchedRequestID(SentryIgnoredException):
    """Exception raised when the returned request ID doesn't match the saved ID."""


class InvalidSignature(SentryIgnoredException):
    """Signature of XML Object is either missing or invalid"""
