"""Common SAML Exceptions"""

from django.utils.translation import gettext_lazy as _

from authentik.lib.tracing.exceptions import TracingIgnoredException

ERROR_CANNOT_DECODE_REQUEST = _("Cannot decode SAML request.")
ERROR_SIGNATURE_REQUIRED_BUT_ABSENT = _(
    "Verification Certificate configured, but request is not signed."
)
ERROR_FAILED_TO_VERIFY = _("Failed to verify signature")


class CannotHandleAssertion(TracingIgnoredException):
    """This processor does not handle this assertion."""
