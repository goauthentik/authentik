"""Kerberos exceptions"""
from enum import UNIQUE, Enum, verify
from typing import Any

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from pyasn1.type import univ


@verify(UNIQUE)
class ErrorCode(Enum):
    """
    Kerberos error codes as defined by RFC 4120.

    See https://www.rfc-editor.org/rfc/rfc4120#section-7.5.9
    """

    KDC_ERR_NONE = 0  # No error
    KDC_ERR_NAME_EXP = 1  # Client's entry in database has expired
    KDC_ERR_SERVICE_EXP = 2  # Server's entry in database has expired
    KDC_ERR_BAD_PVNO = 3  # Requested protocol version number not supported
    KDC_ERR_C_OLD_MAST_KVNO = 4  # Client's key encrypted in old master key
    KDC_ERR_S_OLD_MAST_KVNO = 5  # Server's key encrypted in old master key
    KDC_ERR_C_PRINCIPAL_UNKNOWN = 6  # Client not found in Kerberos database
    KDC_ERR_S_PRINCIPAL_UNKNOWN = 7  # Server not found in Kerberos database
    KDC_ERR_PRINCIPAL_NOT_UNIQUE = 8  # Multiple principal entries in database
    KDC_ERR_NULL_KEY = 9  # The client or server has a null key
    KDC_ERR_CANNOT_POSTDATE = 10  # Ticket not eligible for postdating
    KDC_ERR_NEVER_VALID = 11  # Requested starttime is later than end time
    KDC_ERR_POLICY = 12  # KDC policy rejects request
    KDC_ERR_BADOPTION = 13  # KDC cannot accommodate requested option
    KDC_ERR_ETYPE_NOSUPP = 14  # KDC has no support for encryption type
    KDC_ERR_SUMTYPE_NOSUPP = 15  # KDC has no support for checksum type
    KDC_ERR_PADATA_TYPE_NOSUPP = 16  # KDC has no support for padata type
    KDC_ERR_TRTYPE_NOSUPP = 17  # KDC has no support for transited type
    KDC_ERR_CLIENT_REVOKED = 18  # Clients credentials have been revoked
    KDC_ERR_SERVICE_REVOKED = 19  # Credentials for server have been revoked
    KDC_ERR_TGT_REVOKED = 20  # TGT has been revoked
    KDC_ERR_CLIENT_NOTYET = 21  # Client not yet valid; try again later
    KDC_ERR_SERVICE_NOTYET = 22  # Server not yet valid; try again later
    KDC_ERR_KEY_EXPIRED = 23  # Password has expired; change password to reset
    KDC_ERR_PREAUTH_FAILED = 24  # Pre-authentication information was invalid
    KDC_ERR_PREAUTH_REQUIRED = 25  # Additional pre-authentication required
    KDC_ERR_SERVER_NOMATCH = 26  # Requested server and ticket don't match
    KDC_ERR_MUST_USE_USER2USER = 27  # Server principal valid for user2user only
    KDC_ERR_PATH_NOT_ACCEPTED = 28  # KDC Policy rejects transited path
    KDC_ERR_SVC_UNAVAILABLE = 29  # A service is not available
    KRB_AP_ERR_BAD_INTEGRITY = 31  # Integrity check on decrypted field failed
    KRB_AP_ERR_TKT_EXPIRED = 32  # Ticket expired
    KRB_AP_ERR_TKT_NYV = 33  # Ticket not yet valid
    KRB_AP_ERR_REPEAT = 34  # Request is a replay
    KRB_AP_ERR_NOT_US = 35  # The ticket isn't for us
    KRB_AP_ERR_BADMATCH = 36  # Ticket and authenticator don't match
    KRB_AP_ERR_SKEW = 37  # Clock skew too great
    KRB_AP_ERR_BADADDR = 38  # Incorrect net address
    KRB_AP_ERR_BADVERSION = 39  # Protocol version mismatch
    KRB_AP_ERR_MSG_TYPE = 40  # Invalid msg type
    KRB_AP_ERR_MODIFIED = 41  # Message stream modified
    KRB_AP_ERR_BADORDER = 42  # Message out of order
    KRB_AP_ERR_BADKEYVER = 44  # Specified version of key is not available
    KRB_AP_ERR_NOKEY = 45  # Service key not available
    KRB_AP_ERR_MUT_FAIL = 46  # Mutual authentication failed
    KRB_AP_ERR_BADDIRECTION = 47  # Incorrect message direction
    KRB_AP_ERR_METHOD = 48  # Alternative authentication method required
    KRB_AP_ERR_BADSEQ = 49  # Incorrect sequence number in message
    KRB_AP_ERR_INAPP_CKSUM = 50  # Inappropriate type of checksum in message
    KRB_AP_PATH_NOT_ACCEPTED = 51  # Policy rejects transited path
    KRB_ERR_RESPONSE_TOO_BIG = 52  # Response too big for UDP; retry with TCP
    KRB_ERR_GENERIC = 60  # Generic error (description in e-text)
    KRB_ERR_FIELD_TOOLONG = 61  # Field is too long for this implementation
    KDC_ERROR_CLIENT_NOT_TRUSTED = 62  # Reserved for PKINIT
    KDC_ERROR_KDC_NOT_TRUSTED = 63  # Reserved for PKINIT
    KDC_ERROR_INVALID_SIG = 64  # Reserved for PKINIT
    KDC_ERR_KEY_TOO_WEAK = 65  # Reserved for PKINIT
    KDC_ERR_CERTIFICATE_MISMATCH = 66  # Reserved for PKINIT
    KRB_AP_ERR_NO_TGT = 67  # No TGT available to validate USER-TO-USER
    KDC_ERR_WRONG_REALM = 68  # Reserved for future use
    KRB_AP_ERR_USER_TO_USER_REQUIRED = 69  # Ticket must be for USER-TO-USER
    KDC_ERR_CANT_VERIFY_CERTIFICATE = 70  # Reserved for PKINIT
    KDC_ERR_INVALID_CERTIFICATE = 71  # Reserved for PKINIT
    KDC_ERR_REVOKED_CERTIFICATE = 72  # Reserved for PKINIT
    KDC_ERR_REVOCATION_STATUS_UNKNOWN = 73  # Reserved for PKINIT
    KDC_ERR_REVOCATION_STATUS_UNAVAILABLE = 74  # Reserved for PKINIT
    KDC_ERR_CLIENT_NAME_MISMATCH = 75  # Reserved for PKINIT
    KDC_ERR_KDC_NAME_MISMATCH = 76  # Reserved for PKINIT
    KDC_ERR_INCONSISTENT_KEY_PURPOSE = 77  # Reserved for PKINIT
    KDC_ERR_DIGEST_IN_CERT_NOT_ACCEPTED = 78  # Reserved for PKINIT
    KDC_ERR_PA_CHECKSUM_MUST_BE_INCLUDED = 79  # Reserved for PKINIT
    KDC_ERR_DIGEST_IN_SIGNED_DATA_NOT_ACCEPTED = 80  # Reserved for PKINIT
    KDC_ERR_PUBLIC_KEY_ENCRYPTION_NOT_SUPPORTED = 81  # Reserved for PKINIT
    KDC_ERR_PREAUTH_EXPIRED = 90  # Pre-authentication has expired
    KDC_ERR_MORE_PREAUTH_DATA_REQUIRED = 91  # Additional pre-authentication data is required
    KDC_ERR_PREAUTH_BAD_AUTHENTICATION_SET = (
        92  # KDC cannot accommodate requested pre-authentication data element
    )
    KDC_ERR_UNKNOWN_CRITICAL_FAST_OPTIONS = 93  # Reserved for PKINIT


ERROR_MESSAGES = {
    ErrorCode.KDC_ERR_NONE: _("No error"),
    ErrorCode.KDC_ERR_NAME_EXP: _("Client's entry in database has expired"),
    ErrorCode.KDC_ERR_SERVICE_EXP: _("Server's entry in database has expired"),
    ErrorCode.KDC_ERR_BAD_PVNO: _("Requested protocol version number not supported"),
    ErrorCode.KDC_ERR_C_OLD_MAST_KVNO: _("Client's key encrypted in old master key"),
    ErrorCode.KDC_ERR_S_OLD_MAST_KVNO: _("Server's key encrypted in old master key"),
    ErrorCode.KDC_ERR_C_PRINCIPAL_UNKNOWN: _("Client not found in Kerberos database"),
    ErrorCode.KDC_ERR_S_PRINCIPAL_UNKNOWN: _("Server not found in Kerberos database"),
    ErrorCode.KDC_ERR_PRINCIPAL_NOT_UNIQUE: _("Multiple principal entries in database"),
    ErrorCode.KDC_ERR_NULL_KEY: _("The client or server has a null key"),
    ErrorCode.KDC_ERR_CANNOT_POSTDATE: _("Ticket not eligible for postdating"),
    ErrorCode.KDC_ERR_NEVER_VALID: _("Requested starttime is later than end time"),
    ErrorCode.KDC_ERR_POLICY: _("KDC policy rejects request"),
    ErrorCode.KDC_ERR_BADOPTION: _("KDC cannot accommodate requested option"),
    ErrorCode.KDC_ERR_ETYPE_NOSUPP: _("KDC has no support for encryption type"),
    ErrorCode.KDC_ERR_SUMTYPE_NOSUPP: _("KDC has no support for checksum type"),
    ErrorCode.KDC_ERR_PADATA_TYPE_NOSUPP: _("KDC has no support for padata type"),
    ErrorCode.KDC_ERR_TRTYPE_NOSUPP: _("KDC has no support for transited type"),
    ErrorCode.KDC_ERR_CLIENT_REVOKED: _("Clients credentials have been revoked"),
    ErrorCode.KDC_ERR_SERVICE_REVOKED: _("Credentials for server have been revoked"),
    ErrorCode.KDC_ERR_TGT_REVOKED: _("TGT has been revoked"),
    ErrorCode.KDC_ERR_CLIENT_NOTYET: _("Client not yet valid; try again later"),
    ErrorCode.KDC_ERR_SERVICE_NOTYET: _("Server not yet valid; try again later"),
    ErrorCode.KDC_ERR_KEY_EXPIRED: _("Password has expired; change password to reset"),
    ErrorCode.KDC_ERR_PREAUTH_FAILED: _("Pre-authentication information was invalid"),
    ErrorCode.KDC_ERR_PREAUTH_REQUIRED: _("Additional pre-authentication required"),
    ErrorCode.KDC_ERR_SERVER_NOMATCH: _("Requested server and ticket don't match"),
    ErrorCode.KDC_ERR_MUST_USE_USER2USER: _("Server principal valid for user2user only"),
    ErrorCode.KDC_ERR_PATH_NOT_ACCEPTED: _("KDC Policy rejects transited path"),
    ErrorCode.KDC_ERR_SVC_UNAVAILABLE: _("A service is not available"),
    ErrorCode.KRB_AP_ERR_BAD_INTEGRITY: _("Integrity check on decrypted field failed"),
    ErrorCode.KRB_AP_ERR_TKT_EXPIRED: _("Ticket expired"),
    ErrorCode.KRB_AP_ERR_TKT_NYV: _("Ticket not yet valid"),
    ErrorCode.KRB_AP_ERR_REPEAT: _("Request is a replay"),
    ErrorCode.KRB_AP_ERR_NOT_US: _("The ticket isn't for us"),
    ErrorCode.KRB_AP_ERR_BADMATCH: _("Ticket and authenticator don't match"),
    ErrorCode.KRB_AP_ERR_SKEW: _("Clock skew too great"),
    ErrorCode.KRB_AP_ERR_BADADDR: _("Incorrect net address"),
    ErrorCode.KRB_AP_ERR_BADVERSION: _("Protocol version mismatch"),
    ErrorCode.KRB_AP_ERR_MSG_TYPE: _("Invalid msg type"),
    ErrorCode.KRB_AP_ERR_MODIFIED: _("Message stream modified"),
    ErrorCode.KRB_AP_ERR_BADORDER: _("Message out of order"),
    ErrorCode.KRB_AP_ERR_BADKEYVER: _("Specified version of key is not available"),
    ErrorCode.KRB_AP_ERR_NOKEY: _("Service key not available"),
    ErrorCode.KRB_AP_ERR_MUT_FAIL: _("Mutual authentication failed"),
    ErrorCode.KRB_AP_ERR_BADDIRECTION: _("Incorrect message direction"),
    ErrorCode.KRB_AP_ERR_METHOD: _("Alternative authentication method required"),
    ErrorCode.KRB_AP_ERR_BADSEQ: _("Incorrect sequence number in message"),
    ErrorCode.KRB_AP_ERR_INAPP_CKSUM: _("Inappropriate type of checksum in message"),
    ErrorCode.KRB_AP_PATH_NOT_ACCEPTED: _("Policy rejects transited path"),
    ErrorCode.KRB_ERR_RESPONSE_TOO_BIG: _("Response too big for UDP; retry with TCP"),
    ErrorCode.KRB_ERR_GENERIC: _("Generic error (description in e-text)"),
    ErrorCode.KRB_ERR_FIELD_TOOLONG: _("Field is too long for this implementation"),
    ErrorCode.KDC_ERROR_CLIENT_NOT_TRUSTED: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERROR_KDC_NOT_TRUSTED: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERROR_INVALID_SIG: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_KEY_TOO_WEAK: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_CERTIFICATE_MISMATCH: _("Reserved for PKINIT"),
    ErrorCode.KRB_AP_ERR_NO_TGT: _("No TGT available to validate USER-TO-USER"),
    ErrorCode.KDC_ERR_WRONG_REALM: _("Reserved for future use"),
    ErrorCode.KRB_AP_ERR_USER_TO_USER_REQUIRED: _("Ticket must be for USER-TO-USER"),
    ErrorCode.KDC_ERR_CANT_VERIFY_CERTIFICATE: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_INVALID_CERTIFICATE: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_REVOKED_CERTIFICATE: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_REVOCATION_STATUS_UNKNOWN: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_REVOCATION_STATUS_UNAVAILABLE: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_CLIENT_NAME_MISMATCH: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_KDC_NAME_MISMATCH: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_INCONSISTENT_KEY_PURPOSE: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_DIGEST_IN_CERT_NOT_ACCEPTED: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_PA_CHECKSUM_MUST_BE_INCLUDED: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_DIGEST_IN_SIGNED_DATA_NOT_ACCEPTED: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_PUBLIC_KEY_ENCRYPTION_NOT_SUPPORTED: _("Reserved for PKINIT"),
    ErrorCode.KDC_ERR_PREAUTH_EXPIRED: _("Pre-authentication has expired"),
    ErrorCode.KDC_ERR_MORE_PREAUTH_DATA_REQUIRED: _(
        "Additional pre-authentication data is required"
    ),
    ErrorCode.KDC_ERR_PREAUTH_BAD_AUTHENTICATION_SET: _(
        "KDC cannot accommodate requested pre-authentication data element"
    ),
    ErrorCode.KDC_ERR_UNKNOWN_CRITICAL_FAST_OPTIONS: _("Reserved for PKINIT"),
}


class KerberosError(Exception):
    """Kerberos generic exception"""

    Code = ErrorCode

    def __init__(
        self,
        code: ErrorCode = ErrorCode.KRB_ERR_GENERIC,
        context: dict[str, Any] | None = None,
        message: str | None = None,
    ):
        self.code = code
        self.context = context or {}
        self.message = message or ERROR_MESSAGES[code]
        super().__init__(self.message)

    # We cannot type annotate classes in protocol.py because of circular imports
    def to_krberror(self, realm: str, sname: Any, **context) -> Any:
        """Convert exception to a protocol error."""
        # pylint: disable=import-outside-toplevel
        from authentik.providers.kerberos.lib import protocol

        self.context.update(context)
        obj = protocol.KrbError()
        obj["pvno"] = protocol.KERBEROS_VERSION
        obj["msg-type"] = protocol.ApplicationTag.KRB_ERROR.value
        obj["stime"] = str(obj["stime"].fromDateTime(now()))
        obj["susec"] = now().microsecond
        obj["error-code"] = self.code.value
        obj["realm"] = realm
        obj["sname"].setComponents(*sname.components)
        obj["e-text"] = self.message
        for k in ("ctime", "cusec", "crealm", "cname", "e-data"):
            if k in self.context:
                if isinstance(obj[k], univ.Sequence):
                    obj[k].setComponents(*self.context[k].components)
                else:
                    obj[k] = self.context[k]
        return obj
