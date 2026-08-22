"""authentik SAML IDP Exceptions"""

from authentik.lib.tracing import TracingIgnoredException


class CannotHandleAssertion(TracingIgnoredException):
    """This processor does not handle this assertion."""
