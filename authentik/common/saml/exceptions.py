"""Common SAML Exceptions"""

from django.utils.translation import gettext_lazy as _

from authentik.lib.tracing.exceptions import TracingIgnoredException

ERROR_CANNOT_DECODE_REQUEST = _("Cannot decode SAML request.")
ERROR_SIGNATURE_REQUIRED_BUT_ABSENT = _(
    "Verification Certificate configured, but request is not signed."
)
ERROR_FAILED_TO_VERIFY = _("Failed to verify signature")
ERROR_ACS_URL_MISMATCH = _(
    "The ACS URL in the request does not match the ACS URL configured on the provider."
)


class CannotHandleAssertion(TracingIgnoredException):
    """This processor does not handle this assertion.

    `message` is shown to the user and must not contain request contents or internals.
    `detail` is only logged and recorded in events for administrators."""

    def __init__(self, message: str, detail: str | None = None):
        super().__init__(message)
        self.detail = detail
