"""passbook saml source exceptions"""


class MissingSAMLResponse(Exception):
    """Exception raised when request does not contain SAML Response."""


class UnsupportedNameIDFormat(Exception):
    """Exception raised when SAML Response contains NameID Format not supported."""
