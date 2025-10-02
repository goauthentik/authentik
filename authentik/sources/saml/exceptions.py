"""authentik saml source exceptions"""

from authentik.lib.sentry import SentryIgnoredException


class SAMLException(SentryIgnoredException):
    """Base SAML Exception"""

    default_message = "An unspecified SAML error occurred."

    def __str__(self):
        if self.args:
            return super().__str__()
        return self.default_message


class MissingSAMLResponse(SAMLException):
    """Exception raised when request does not contain SAML Response."""

    default_message = "Request does not contain a SAML response."


class UnsupportedNameIDFormat(SAMLException):
    """Exception raised when SAML Response contains NameID Format not supported."""

    default_message = "The NameID Format in the SAML Response is not supported."


class MismatchedRequestID(SAMLException):
    """Exception raised when the returned request ID doesn't match the saved ID."""

    default_message = "The SAML Response ID does not match the original request ID."


class InvalidEncryption(SAMLException):
    """Encryption of XML Object is either missing or invalid."""

    default_message = "The encryption of the SAML object is either missing or invalid."


class InvalidSignature(SAMLException):
    """Signature of XML Object is either missing or invalid."""

    default_message = "The signature of the SAML object is either missing or invalid."
