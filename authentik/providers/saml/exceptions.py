"""authentik SAML IDP Exceptions"""

from authentik.lib.otel import TracingIgnoredException


class CannotHandleAssertion(TracingIgnoredException):
    """This processor does not handle this assertion."""
