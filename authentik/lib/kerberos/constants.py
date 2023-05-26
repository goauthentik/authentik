from enum import UNIQUE, Enum, verify


@verify(UNIQUE)
class PrincipalNameType(Enum):
    """
    Kerberos principal name types as defined by RFC 4120 and RFC 6111.

    See https://www.rfc-editor.org/rfc/rfc4120#section-6.2 and https://www.rfc-editor.org/rfc/rfc6111.html#section-3.1
    """

    # Name type not known
    NT_UNKNOWN = 0
    # Just the name of the principal as in DCE, or for users
    NT_PRINCIPAL = 1
    # Service and other unique instance (krbtgt)
    NT_SRV_INST = 2
    # Service with host name as instance (telnet, rcommands)
    NT_SRV_HST = 3
    # Service with host as remaining components
    NT_SRV_XHST = 4
    # Unique ID
    NT_UID = 5
    # Encoded X.509 Distinguished Name
    NT_X500_PRINCIPAL = 6
    # Name in form of SMTP email name (e.g., user@example.com)
    NT_SMTP_NAME = 7
    # Enterprise name
    NT_ENTERPRISE = 10
    # Name considered well-known
    NT_WELLKNOWN = 11
