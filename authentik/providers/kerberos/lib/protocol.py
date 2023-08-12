"""
Kerberos protocol primitives for ASN.1 encoding and decoding.

Allows for decoding types specified in RFC 4120.

See https://www.rfc-editor.org/rfc/rfc4120#section-3
"""
# pylint: disable=too-many-ancestors
import socket
from collections import UserDict
from datetime import datetime, timezone
from enum import UNIQUE, IntEnum, verify
from typing import Any, Self

from pyasn1.codec.der.decoder import decode as der_decode
from pyasn1.codec.der.encoder import encode as der_encode
from pyasn1.codec.native.decoder import decode as native_decode
from pyasn1.codec.native.encoder import encode as native_encode
from pyasn1.error import PyAsn1Error
from pyasn1.type import base, char, constraint, namedtype, namedval, tag, univ, useful
from structlog.stdlib import get_logger

from authentik.providers.kerberos.lib import crypto
from authentik.providers.kerberos.lib.exceptions import KerberosError

LOGGER = get_logger()


KERBEROS_PVNO = 5


@verify(UNIQUE)
class KeyUsageNumbers(IntEnum):
    """Kerberos key usage numbers as defined by RFC 4120

    See https://www.rfc-editor.org/rfc/rfc4120#section-7.5.1
    """

    AS_REQ_PA_ENC_TIMESTAMP = 1
    KDC_REP_TICKET = 2
    AS_REP_ENCPART = 3
    TGS_REQ_KDC_REQ_BODY_AUTHDATA_SESSION_KEY = 4
    TGS_REQ_KDC_REQ_BODY_AUTHDATA_SUB_KEY = 5
    TGS_REQ_PA_TGS_REQ_AP_REQ_AUTHENTICATOR_CHKSUM = 6
    TGS_REQ_PA_TGS_REQ_AP_REQ_AUTHENTICATOR = 7
    TGS_REP_ENCPART_SESSION_KEY = 8
    TGS_REP_ENCPART_AUTHENTICATOR_SUB_KEY = 9
    AP_REQ_AUTHENTICATOR_CHKSUM = 10
    AP_REQ_AUTHENTICATOR = 11
    AP_REP_ENCPART = 12
    KRB_PRIV_ENCPART = 13
    KRB_CRED_ENCPART = 14
    KRB_SAFE_CHKSUM = 15
    KERB_NON_KERB_SALT = 16
    KERB_NON_KERB_CKSUM_SALT = 17
    # 18.  Reserved for future use in Kerberos and related protocols.
    AD_KDC_ISSUED_CHKSUM = 19
    # 20-21.  Reserved for future use in Kerberos and related protocols.
    GSSAPI_ACCEPTOR_SEAL = 22
    GSSAPI_ACCEPTOR_SIGN = 23
    GSSAPI_INITIATOR_SEAL = 24
    GSSAPI_INITIATOR_SIGN = 25
    KEY_USAGE_FAST_REQ_CHKSUM = 50
    KEY_USAGE_FAST_ENC = 51
    KEY_USAGE_FAST_REP = 52
    KEY_USAGE_FAST_FINISHED = 53
    KEY_USAGE_ENC_CHALLENGE_CLIENT = 54
    KEY_USAGE_ENC_CHALLENGE_KDC = 55
    KEY_USAGE_AS_REQ = 56
    # 26-511.  Reserved for future use in Kerberos and related protocols.
    # 512-1023.  Reserved for uses internal to a Kerberos implementation.
    # 1024.  Encryption for application use in protocols that do not specify key usage values
    # 1025.  Checksums for application use in protocols that do not specify key usage values
    # 1026-2047.  Reserved for application use.


@verify(UNIQUE)
class PrincipalNameType(IntEnum):
    """
    Kerberos principal name types as defined by RFC 4120 and RFC 6111.

    See https://www.rfc-editor.org/rfc/rfc4120#section-6.2
    and https://www.rfc-editor.org/rfc/rfc6111.html#section-3.1
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


@verify(UNIQUE)
class ApplicationTag(IntEnum):
    """
    Kerberos messages ASN.1 application tags as defined by RFC 4120 and RFC 6111.

    See https://www.rfc-editor.org/rfc/rfc4120#section-3
    """

    # 0: Unused
    TICKET = 1  # PDU
    AUTHENTICATOR = 2  # non-PDU
    ENC_TICKET_PART = 3  # non-PDU
    # 4-9: Unused
    AS_REQ = 10  # PDU
    AS_REP = 11  # PDU
    TGS_REQ = 12  # PDU
    TGS_REP = 13  # PDU
    AP_REQ = 14  # PDU
    AP_REP = 15  # PDU
    RESERVED16 = 16  # TGT-REQ (for user-to-user)
    RESERVED17 = 17  # TGT-REP (for user-to-user)
    # 18-19: Unused
    KRB_SAFE = 20  # PDU
    KRB_PRIV = 21  # PDU
    KRB_CRED = 22  # PDU
    # 23-24: Unused
    ENC_AS_REP_PART = 25  # non-PDU
    ENC_TGS_REP_PART = 26  # non-PDU
    ENC_AP_REP_PART = 27  # non-PDU
    ENC_KRB_PRIV_PART = 28  # non-PDU
    ENC_KRB_CRED_PART = 29  # non-PDU
    KRB_ERROR = 30  # PDU


def _application_tag(tag_: ApplicationTag) -> tag.TagSet:
    return univ.Sequence.tagSet.tagExplicitly(
        tag.Tag(tag.tagClassApplication, tag.tagFormatConstructed, tag_)
    )


def _sequence_component(
    name: str, tag_value: int, type_: base.Asn1Type, **subkwargs
) -> namedtype.NamedType:
    return namedtype.NamedType(
        name,
        type_.subtype(
            explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, tag_value), **subkwargs
        ),
    )


def _sequence_optional_component(
    name: str, tag_value: int, type_: base.Asn1Type, **subkwargs
) -> namedtype.OptionalNamedType:
    return namedtype.OptionalNamedType(
        name,
        type_.subtype(
            explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, tag_value), **subkwargs
        ),
    )


def _kvno_component(name: str, tag_value: int) -> namedtype.NamedType:
    return _sequence_component(
        name, tag_value, univ.Integer(), subtypeSpec=constraint.ValueRangeConstraint(5, 5)
    )


class Asn1SetValueMixin:
    """pyasn1 Sequence mixin to allow for easier interaction with stored data."""

    @classmethod
    def from_values(cls, **kwargs) -> Self:
        """Create ASN.1 object from arguments."""
        obj = cls()
        for name, value in kwargs.items():
            if value is None:
                continue
            name = name.replace("_", "-")
            obj.set_value(name, value)
        return obj

    def set_value(self, name: str, value: Any) -> Any:
        """Set an attribute, but do if without having to monkey around with tagsets."""
        if hasattr(self[name], "setComponents") and hasattr(value, "components"):
            self[name].setComponents(*value.components)
        elif hasattr(value, "tagSet"):
            self[name] = value.clone(tagSet=self[name].tagSet)
        elif isinstance(value, datetime):
            self[name] = str(self[name].fromDateTime(value))
        else:
            self[name] = value
        return self[name]


class Asn1LeafMixin:
    """pyasn1 mixin for exporting and importing data."""

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """Decode data into an ASN.1 object."""
        try:
            req, tail = der_decode(data, asn1Spec=cls())
        except PyAsn1Error as exc:
            raise KerberosError(message=f"Fail parsing {cls.__name__}") from exc
        if tail:
            raise KerberosError(message=f"Extra data found when parsing {cls.__name__}")
        return req

    def to_bytes(self) -> bytes:
        """Encode an ASN.1 object."""
        return der_encode(self)


class Sequence(univ.Sequence):
    def from_python(self, obj: Any) -> Self:
        asn1obj = self.clone()
        for key in asn1obj:
            if key in obj and obj[key] is not None:
                if hasattr(asn1obj[key], "from_python"):
                    asn1obj[key] = asn1obj[key].from_python(obj[key])
                elif hasattr(obj[key], "to_asn1"):
                    asn1obj[key] = obj[key].to_asn1()
                else:
                    asn1obj[key] = native_decode(obj[key], asn1obj[key])
        return asn1obj

    def to_python(self) -> dict[str, Any]:
        obj = {}
        for key in self:
            if not self[key].isValue:
                continue
            elif hasattr(self[key], "to_python"):
                obj[key] = self[key].to_python()
            else:
                obj[key] = native_encode(self[key])
        return obj


class SequenceOf(univ.SequenceOf):
    def from_python(self, obj: Any) -> Self:
        asn1obj = self.clone()
        for value in obj:
            if hasattr(asn1obj.componentType, "from_python"):
                asn1obj.append(asn1obj.componentType.from_python(value))
            elif hasattr(value, "to_asn1"):
                asn1obj.append(value.to_asn1())
            else:
                asn1obj.append(native_decode(value, asn1obj.componentType))
        return asn1obj

    def to_python(self) -> list[Any]:
        obj = []
        if not self.isValue:
            return []
        for value in self:
            if hasattr(value, "to_python"):
                obj.append(value.to_python())
            else:
                obj.append(native_encode(value))
        return obj


class Int32(univ.Integer):
    """Kerberos Int32 ASN.1 representation."""

    subtypeSpec = univ.Integer.subtypeSpec + constraint.ValueRangeConstraint(
        -2147483648, 2147483647
    )

    def to_bytes(self, *args, **kwargs) -> bytes:
        """Encode an ASN.1 object."""
        return int(self).to_bytes(*args, **kwargs)


class UInt32(univ.Integer):
    """Kerberos UInt32 ASN.1 representation."""

    subtypeSpec = univ.Integer.subtypeSpec + constraint.ValueRangeConstraint(0, 4294967295)


class Microseconds(univ.Integer):
    """Kerberos Microseconds ASN.1 representation."""

    subtypeSpec = univ.Integer.subtypeSpec + constraint.ValueRangeConstraint(0, 999999)


class KerberosString(char.GeneralString):
    """Kerberos string ASN.1 representation"""

    def to_python(self):
        return str(self)


class Realm(KerberosString):
    """Kerberos Realm ASN.1 representation"""


class PrincipalName(Asn1SetValueMixin, Sequence):
    """Kerberos principal name ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("name-type", 0, Int32()),
        _sequence_component("name-string", 1, SequenceOf(componentType=KerberosString())),
    )

    def to_python(self):
        return self.to_string()

    def from_python(self, value: str) -> Self:
        principal = self.from_spn(value)
        return super().from_python(
            {
                "name-type": principal["name-type"],
                "name-string": principal["name-string"],
            }
        )

    def to_string(self):
        """Format the principal name."""
        return "/".join([str(name) for name in self["name-string"]])

    @classmethod
    def from_components(cls, name_type: PrincipalNameType, name: list[str]) -> Self:
        """Create a principal name from name components."""
        obj = cls()
        obj["name-type"] = name_type
        obj["name-string"].extend(name)
        return obj

    @classmethod
    def from_spn(cls, spn: str) -> Self:
        """Create a principal name from a service principal name."""
        name, realm, *_ = spn.rsplit("@", maxsplit=1) + [None]
        components = name.split("/")
        if realm == "":
            raise ValueError("Empty realms are not allowed")
        if not all(components):
            raise ValueError("Empty names are not allowed")
        match len(components):
            case 1:
                name_type = PrincipalNameType.NT_SRV_INST
            case 2:
                name_type = PrincipalNameType.NT_SRV_HST
            case _:
                name_type = PrincipalNameType.NT_SRV_XHST
        # Special case for krbtgt
        if components[0] == "krbtgt":
            name_type = PrincipalNameType.NT_SRV_INST
        return cls.from_components(name_type, components)

    @classmethod
    def krbtgt(cls, realm: str) -> Self:
        """Create a krbtgt principal name from a realm."""
        return cls.from_components(PrincipalNameType.NT_SRV_INST, ["krbtgt", realm])


class KerberosTime(useful.GeneralizedTime):
    """Kerberos time ASN.1 representation"""

    _hasSubsecond = False

    def from_python(self, value: Any) -> Self:
        return native_decode(value.astimezone(tz=timezone.utc).strftime("%Y%m%d%H%M%SZ"), self)

    def to_python(self):
        return self.asDateTime.replace(tzinfo=timezone.utc)


class HostAddress(Sequence):
    """Kerberos host address ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("addr-type", 0, Int32()),
        _sequence_component("address", 1, univ.OctetString()),
    )

    def from_python(self, value: tuple[int, str | bytes]) -> Self:
        addr_type, addr_value = value
        if addr_type == 2:  # TODO: make constant
            addr_value = socket.inet_pton(socket.AF_INET, addr_value)
        elif addr_type == 24:  # TODO: make constant
            addr_value = socket.inet_pton(socket.AF_INET6, addr_value)
        return super().from_python(
            {
                "addr-type": addr_type,
                "address": addr_value,
            }
        )

    def to_python(self):
        addr = bytes(self["address"])
        if self["addr-type"] == 2:  # TODO: make constant
            addr = socket.inet_ntop(socket.AF_INET, addr)
        elif self["addr-type"] == 24:  # TODO: make constant
            addr = socket.inet_ntop(socket.AF_INET6, addr)
        return (int(self["addr-type"]), addr)


class HostAddresses(SequenceOf):
    """Kerberos host addresses ASN.1 reprensentation"""

    componentType = HostAddress()


class AuthorizationData(SequenceOf):
    """Kerberos Authorization Data ASN.1 representation."""

    componentType = Sequence(
        componentType=namedtype.NamedTypes(
            _sequence_component("ad-type", 0, Int32()),
            _sequence_component("ad-data", 1, univ.OctetString()),
        )
    )


class LastReq(SequenceOf):
    """Kerberos Last Req ASN.1 representation."""

    componentType = Sequence(
        componentType=namedtype.NamedTypes(
            _sequence_component("lr-type", 0, Int32()),
            _sequence_component("lr-data", 1, KerberosTime()),
        )
    )


class PaDataEncTsEnc(Asn1LeafMixin, Sequence):
    """Kerberos PaData EncTsEnc ASN.1 representation."""

    componentType = namedtype.NamedTypes(
        _sequence_component("patimestamp", 0, KerberosTime()),
        _sequence_optional_component("pausec", 1, Microseconds()),
    )


class EncryptionType(Int32):
    def from_python(self, value: Any) -> Self:
        if issubclass(value, crypto.EncryptionType):
            return native_decode(value.ENC_TYPE, self)
        return native_decode(value[0], self)

    def to_python(self):
        try:
            return (int(self), crypto.get_enctype_from_value(self))
        except IndexError:
            return (int(self), None)


class PaDataEtypeInfo2Entry(Sequence):
    """Kerberos PaData ETypeInfo2 Entry ASN.1 representation."""

    componentType = namedtype.NamedTypes(
        _sequence_component("etype", 0, EncryptionType()),
        _sequence_optional_component("salt", 1, KerberosString()),
        _sequence_optional_component("s2kparams", 2, univ.OctetString()),
    )


class PaDataEtypeInfo2(Asn1LeafMixin, SequenceOf):
    """Kerberos PaData ETypeInfo2 ASN.1 representation."""

    componentType = PaDataEtypeInfo2Entry()


class PaData(Sequence):
    """Kerberos PA Data ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("padata-type", 1, Int32()),
        _sequence_component("padata-value", 2, univ.OctetString()),
    )

    def from_python(self, value: tuple[int, bytes]) -> Self:
        return super().from_python(
            {
                "padata-type": value[0],
                "padata-value": value[1],
            }
        )

    def to_python(self) -> type[int, bytes]:
        return (int(self["padata-type"]), bytes(self["padata-value"]))


class MethodData(Asn1LeafMixin, SequenceOf):
    """Kerberos Method Data ASN.1 representation."""

    componentType = PaData()


class KerberosFlags(univ.BitString):
    """Kerberos flags ASN.1 representation"""

    bitLength = 32

    def __init__(self, value=univ.noValue, **kwargs):
        if value is univ.noValue:
            value = univ.SizedInteger(0).setBitLength(self.bitLength)
        super().__init__(value, **kwargs)
        self._value.setBitLength(self.bitLength)

    def __getitem__(self, key):
        if isinstance(key, str):
            key = dict(self.namedValues)[key]
        return bool(super().__getitem__(key))

    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = dict(self.namedValues)[key]
        if key > len(self._value) or key < 0:
            raise IndexError("bit index out of range")
        if value:
            newval = univ.SizedInteger(self._value | (1 << (self.bitLength - key - 1)))
        else:
            newval = univ.SizedInteger(self._value & ~(1 << (self.bitLength - key - 1)))
        newval.setBitLength(self.bitLength)
        self._value = newval
        return self

    def from_python(self, value: dict[str | int, bool]) -> Self:
        obj = self.clone(value=0)
        for flag, flag_val in value.items():
            obj[flag] = flag_val
        return obj

    def to_python(self):
        obj = {}
        for fname in self.namedValues:
            obj[fname] = self[fname]
        return obj


class EncryptedDataWrapper(UserDict):
    def encrypt(self, key: bytes, usage: KeyUsageNumbers, asn1item: Any) -> bytes:
        if issubclass(self["etype"], crypto.EncryptionType):
            etype = self["etype"]
        else:
            etype = self["etype"][1]
        if etype is None:
            raise ValueError("Unsupported enctype")
        self["cipher"] = etype.encrypt_message(
            key=key,
            message=asn1item.from_python(self["plain"]).to_bytes(),
            usage=usage,
        )
        return self["cipher"]

    def decrypt(self, key: bytes, usage: KeyUsageNumbers, plain_cls: Any) -> Any:
        etype = self["etype"][1]
        if etype is None:
            raise ValueError("Unsupported enctype")
        plaintext = etype.decrypt_message(
            key=key,
            ciphertext=self["cipher"],
            usage=usage,
        )
        self["plain"] = plain_cls.from_bytes(plaintext).to_python()
        return self["plain"]


class EncryptedData(Asn1SetValueMixin, Asn1LeafMixin, Sequence):
    """Kerberos encrypted data ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("etype", 0, EncryptionType()),
        _sequence_optional_component("kvno", 1, UInt32()),
        _sequence_component("cipher", 2, univ.OctetString()),
    )

    def to_python(self):
        return EncryptedDataWrapper(super().to_python())


class EncryptionKey(Asn1SetValueMixin, Sequence):
    """Kerberos encryption key ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("keytype", 0, EncryptionType()),
        _sequence_component("keyvalue", 1, univ.OctetString()),
    )


class Checksum(Sequence):
    """Kerberos checksum ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("cksumtype", 0, Int32()),
        _sequence_component("checksum", 1, univ.OctetString()),
    )


class Ticket(Asn1SetValueMixin, Asn1LeafMixin, Sequence):
    """Kerberos ticket ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.TICKET)
    componentType = namedtype.NamedTypes(
        _kvno_component("tkt-vno", 0),
        _sequence_component("realm", 1, Realm()),
        _sequence_component("sname", 2, PrincipalName()),
        _sequence_component("enc-part", 3, EncryptedData()),
    )


class TicketFlags(KerberosFlags):
    """Kerberos ticket flags ASN.1 representation"""

    namedValues = namedval.NamedValues(
        ("reserved", 0),
        ("forwardable", 1),
        ("forwarded", 2),
        ("proxiable", 3),
        ("proxy", 4),
        ("may-postdate", 5),
        ("postdated", 6),
        ("invalid", 7),
        ("renewable", 8),
        ("initial", 9),
        ("pre-authent", 10),
        ("hw-authent", 11),
        ("transited-policy-checked", 12),
        ("ok-as-delegate", 13),
    )


class TransitedEncoding(Asn1SetValueMixin, Sequence):
    """Kerberos transited encoding ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("tr-type", 0, Int32()),
        _sequence_component("contents", 1, univ.OctetString()),
    )


class EncTicketPart(Asn1SetValueMixin, Asn1LeafMixin, Sequence):
    """Kerberos enc ticket part ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.ENC_TICKET_PART)
    componentType = namedtype.NamedTypes(
        _sequence_component("flags", 0, TicketFlags()),
        _sequence_component("key", 1, EncryptionKey()),
        _sequence_component("crealm", 2, Realm()),
        _sequence_component("cname", 3, PrincipalName()),
        _sequence_component("transited", 4, TransitedEncoding()),
        _sequence_component("authtime", 5, KerberosTime()),
        _sequence_optional_component("starttime", 6, KerberosTime()),
        _sequence_component("endtime", 7, KerberosTime()),
        _sequence_optional_component("renew-till", 8, KerberosTime()),
        _sequence_optional_component("caddr", 9, HostAddresses()),
        _sequence_optional_component("authorization-data", 10, AuthorizationData()),
    )


class Authenticator(Asn1LeafMixin, Sequence):
    """Kerberos authenticator ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.AUTHENTICATOR)
    componentType = namedtype.NamedTypes(
        _kvno_component("authenticator-vno", 0),
        _sequence_component("crealm", 1, Realm()),
        _sequence_component("cname", 2, PrincipalName()),
        _sequence_optional_component("cksum", 3, Checksum()),
        _sequence_component("cusec", 4, Microseconds()),
        _sequence_component("ctime", 5, KerberosTime()),
        _sequence_optional_component("subkey", 6, EncryptionKey()),
        _sequence_optional_component("seq-number", 7, UInt32()),
        _sequence_optional_component("authorization-data", 8, AuthorizationData()),
    )


class ApOptions(KerberosFlags):
    """Kerberos AP options ASN.1 representation"""

    namedValues = namedval.NamedValues(
        ("reserved", 0),
        ("use-session-key", 1),
        ("mutual-required", 2),
    )


class KdcOptions(KerberosFlags):
    """Kerberos KDC options ASN.1 representation"""

    namedValues = namedval.NamedValues(
        ("reserved", 0),
        ("forwardable", 1),
        ("forwarded", 2),
        ("proxiable", 3),
        ("proxy", 4),
        ("allow-postdate", 5),
        ("postdated", 6),
        ("unused7", 7),
        ("renewable", 8),
        ("unused9", 9),
        ("unused10", 10),
        ("opt-hardware-auth", 11),
        ("unused12", 12),
        ("unused13", 13),
        ("unused15", 15),
        ("disable-transited-check", 26),
        ("renewable-ok", 27),
        ("enc-tkt-in-skey", 28),
        ("renew", 30),
        ("validate", 31),
    )


class KdcReqBody(Asn1LeafMixin, Sequence):
    """Kerberos KDC req body ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("kdc-options", 0, KdcOptions()),
        _sequence_optional_component("cname", 1, PrincipalName()),
        _sequence_component("realm", 2, Realm()),
        _sequence_optional_component("sname", 3, PrincipalName()),
        _sequence_optional_component("from", 4, KerberosTime()),
        _sequence_component("till", 5, KerberosTime()),
        _sequence_optional_component("rtime", 6, KerberosTime()),
        _sequence_component("nonce", 7, UInt32()),
        _sequence_component("etype", 8, SequenceOf(componentType=EncryptionType())),
        _sequence_optional_component("addresses", 9, HostAddresses()),
        _sequence_optional_component("enc-authorization-data", 10, EncryptedData()),
        _sequence_optional_component("additional-tickets", 11, SequenceOf(componentType=Ticket())),
    )


class KdcReq(Asn1LeafMixin, Sequence):
    """Kerberos KDC req ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _kvno_component("pvno", 1),
        _sequence_component(
            "msg-type",
            2,
            univ.Integer(),
            subtypeSpec=constraint.ConstraintsUnion(
                *(
                    constraint.SingleValueConstraint(v)
                    for v in [ApplicationTag.AS_REQ, ApplicationTag.TGS_REQ]
                )
            ),
        ),
        _sequence_optional_component("padata", 3, SequenceOf(componentType=PaData())),
        _sequence_component("req-body", 4, KdcReqBody()),
    )

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """Decode a KDC REQ into either an AS REQ or a TGS REQ"""
        for subcls in cls.__subclasses__():  # AsReq and TgsReq
            try:
                req, tail = der_decode(data, asn1Spec=subcls())
            except PyAsn1Error as exc:
                LOGGER.debug("failed to parse Kerberos request", exc=exc)
                continue
            if tail:
                raise KerberosError(message="Invalid KdcReq: extra data found")
            return req
        raise KerberosError(message="Invalid KdcReq: unknown MSG_TYPE")


class AsReq(KdcReq):
    """Kerberos AS req ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.AS_REQ)


class TgsReq(KdcReq):
    """Kerberos TGS req ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.TGS_REQ)


class ApReq(Asn1SetValueMixin, Asn1LeafMixin, Sequence):
    """Kerberos AP req ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.AP_REQ)
    componentType = namedtype.NamedTypes(
        _kvno_component("pvno", 0),
        _sequence_component(
            "msg-type",
            1,
            univ.Integer(),
            subtypeSpec=constraint.ConstraintsUnion(
                *(constraint.SingleValueConstraint(v) for v in [ApplicationTag.AP_REQ])
            ),
        ),
        _sequence_component("ap-options", 2, ApOptions()),
        _sequence_component("ticket", 3, Ticket()),
        _sequence_component("authenticator", 4, EncryptedData()),
    )


class KdcRep(Asn1SetValueMixin, Asn1LeafMixin, Sequence):
    """Kerberos Kdc rep ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _kvno_component("pvno", 0),
        _sequence_component(
            "msg-type",
            1,
            univ.Integer(),
            subtypeSpec=constraint.ConstraintsUnion(
                *(
                    constraint.SingleValueConstraint(v)
                    for v in [ApplicationTag.AS_REP, ApplicationTag.TGS_REP]
                )
            ),
        ),
        _sequence_optional_component("padata", 2, SequenceOf(componentType=PaData())),
        _sequence_component("crealm", 3, Realm()),
        _sequence_component("cname", 4, PrincipalName()),
        _sequence_component("ticket", 5, Ticket()),
        _sequence_component("enc-part", 6, EncryptedData()),
    )


class AsRep(KdcRep):
    """Kerberos AS rep ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.AS_REP)


class TgsRep(KdcRep):
    """Kerberos TGS rep ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.TGS_REP)


class EncKdcRepPart(Asn1SetValueMixin, Asn1LeafMixin, Sequence):
    """Kerberos encrypted KDC rep part ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("key", 0, EncryptionKey()),
        _sequence_component("last-req", 1, LastReq()),
        _sequence_component("nonce", 2, UInt32()),
        _sequence_optional_component("key-expiration", 3, KerberosTime()),
        _sequence_component("flags", 4, TicketFlags()),
        _sequence_component("authtime", 5, KerberosTime()),
        _sequence_optional_component("starttime", 6, KerberosTime()),
        _sequence_component("endtime", 7, KerberosTime()),
        _sequence_optional_component("renew-till", 8, KerberosTime()),
        _sequence_component("srealm", 9, Realm()),
        _sequence_component("sname", 10, PrincipalName()),
        _sequence_optional_component("caddr", 11, HostAddresses()),
    )


class EncAsRepPart(EncKdcRepPart):
    """Kerberos encrypted AS rep part ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.ENC_AS_REP_PART)


class EncTgsRepPart(EncKdcRepPart):
    """Kerberos encrypted TGS rep part ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.ENC_TGS_REP_PART)


class KrbError(Asn1SetValueMixin, Asn1LeafMixin, Sequence):
    """Kerberos error ASN.1 representation"""

    tagSet = _application_tag(ApplicationTag.KRB_ERROR)
    componentType = namedtype.NamedTypes(
        _kvno_component("pvno", 0),
        _sequence_component(
            "msg-type",
            1,
            univ.Integer(),
            subtypeSpec=constraint.SingleValueConstraint(ApplicationTag.KRB_ERROR),
        ),
        _sequence_optional_component("ctime", 2, KerberosTime()),
        _sequence_optional_component("cusec", 3, Microseconds()),
        _sequence_component("stime", 4, KerberosTime()),
        _sequence_component("susec", 5, Microseconds()),
        _sequence_component("error-code", 6, Int32()),
        _sequence_optional_component("crealm", 7, Realm()),
        _sequence_optional_component("cname", 8, PrincipalName()),
        _sequence_component("realm", 9, Realm()),
        _sequence_component("sname", 10, PrincipalName()),
        _sequence_optional_component("e-text", 11, KerberosString()),
        _sequence_optional_component("e-data", 12, univ.OctetString()),
    )


class KdcProxyMessage(Asn1LeafMixin, Sequence):
    """Kerberos proxy message ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("message", 0, univ.OctetString()),
        _sequence_optional_component("target-domain", 1, Realm()),
        _sequence_optional_component("dclocator-hint", 2, univ.Integer()),
    )

    def from_python(self, value: dict[str, Any]) -> Self:
        size, message = value.get("message", (0, bytes()))
        value["message"] = size.to_bytes(4, byteorder="big") + message
        return super().from_python(value)

    def to_python(self) -> dict[str, Any]:
        obj = super().to_python()
        obj["message"] = (
            int.from_bytes(
                obj["message"][:4],
                byteorder="big",
            ),
            obj["message"][4:],
        )
        return obj
