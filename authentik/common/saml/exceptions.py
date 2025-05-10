"""authentik saml source exceptions"""

from authentik.common.exceptions import NotReportedException


class SAMLException(NotReportedException):
    """Base SAML Exception"""


class MissingSAMLResponse(SAMLException):
    """Exception raised when request does not contain SAML Response."""


class UnsupportedNameIDFormat(SAMLException):
    """Exception raised when SAML Response contains NameID Format not supported."""


class MismatchedRequestID(SAMLException):
    """Exception raised when the returned request ID doesn't match the saved ID."""


class InvalidEncryption(SAMLException):
    """Encryption of XML Object is either missing or invalid"""


class InvalidSignature(SAMLException):
    """Signature of XML Object is either missing or invalid"""
