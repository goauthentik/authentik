"""Common SAML Exceptions"""

from authentik.lib.tracing.exceptions import TracingIgnoredException

ERROR_CANNOT_DECODE_REQUEST = "Cannot decode SAML request."
ERROR_SIGNATURE_REQUIRED_BUT_ABSENT = (
    "Verification Certificate configured, but request is not signed."
)
ERROR_FAILED_TO_VERIFY = "Failed to verify signature"


class CannotHandleAssertion(TracingIgnoredException):
    """This processor does not handle this assertion."""
