"""authentik SAML IDP Exceptions"""

from authentik.common.exceptions import NotReportedException


class CannotHandleAssertion(NotReportedException):
    """This processor does not handle this assertion."""
