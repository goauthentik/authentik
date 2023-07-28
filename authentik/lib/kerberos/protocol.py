from enum import UNIQUE, Enum, verify
from typing import Self

from pyasn1.codec.der.decoder import decode as der_decode
from pyasn1.codec.der.encoder import encode as der_encode
from pyasn1.error import PyAsn1Error
from pyasn1.type import base, char, constraint, namedtype, namedval, tag, univ, useful

from authentik.lib.kerberos.exceptions import KerberosError

from structlog.stdlib import get_logger
LOGGER = get_logger()


@verify(UNIQUE)
class PrincipalNameType(Enum):
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
class ApplicationTag(Enum):
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
        tag.Tag(tag.tagClassApplication, tag.tagFormatConstructed, tag_.value)
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


class Asn1LeafMixin:
    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        try:
            req, tail = der_decode(data, asn1Spec=cls())
        except PyAsn1Error as exc:
            raise KerberosError(message=f"Fail parsing {cls.__name__}") from exc
        if tail:
            raise KerberosError(message=f"Extra data found when parsing {cls.__name__}")
        return req

    def to_bytes(self) -> bytes:
        return der_encode(self)


class Int32(univ.Integer):
    subtypeSpec = univ.Integer.subtypeSpec + constraint.ValueRangeConstraint(
        -2147483648, 2147483647
    )

    def to_bytes(self, *args, **kwargs) -> bytes:
        return int(self).to_bytes(*args, **kwargs)

class UInt32(univ.Integer):
    subtypeSpec = univ.Integer.subtypeSpec + constraint.ValueRangeConstraint(0, 4294967295)

class Microseconds(univ.Integer):
    subtypeSpec = univ.Integer.subtypeSpec + constraint.ValueRangeConstraint(0, 999999)


class KerberosString(char.GeneralString):
    """Kerberos string ASN.1 representation"""


class Realm(KerberosString):
    """Kerberos Realm ASN.1 representation"""


class PrincipalName(univ.Sequence):
    """Kerberos principal name ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("name-type", 0, Int32()),
        _sequence_component("name-string", 1, univ.SequenceOf(componentType=KerberosString())),
    )

    def to_string(self):
        return "/".join([str(name) for name in self["name-string"]])

    @classmethod
    def from_components(cls, name_type: PrincipalNameType, name: list[str]) -> Self:
        obj = cls()
        obj["name-type"] = name_type.value
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
        return cls.from_components(name_type, components)

class KerberosTime(useful.GeneralizedTime):
    """Kerberos time ASN.1 representation"""

    _hasSubsecond = False


class HostAddress(univ.Sequence):
    """Kerberos host address ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("addr-type", 0, Int32()),
        _sequence_component("address", 1, univ.OctetString()),
    )


class HostAddresses(univ.SequenceOf):
    """Kerberos host addresses ASN.1 reprensentation"""

    componentType = HostAddress()


class AuthorizationData(univ.SequenceOf):
    componentType = univ.Sequence(
        componentType=namedtype.NamedTypes(
            _sequence_component("ad-type", 0, Int32()),
            _sequence_component("ad-data", 1, univ.OctetString()),
        )
    )


class LastReq(univ.SequenceOf):
    componentType = univ.Sequence(
        componentType=namedtype.NamedTypes(
            _sequence_component("lr-type", 0, Int32()),
            _sequence_component("lr-data", 1, KerberosTime()),
        )
    )


class PaDataEncTsEnc(Asn1LeafMixin, univ.Sequence):
    componentType = namedtype.NamedTypes(
        _sequence_component("patimestamp", 0, KerberosTime()),
        _sequence_optional_component("pausec", 1, Microseconds()),
    )


class PaDataEtypeInfo2Entry(univ.Sequence):
    componentType = namedtype.NamedTypes(
        _sequence_component("etype", 0, Int32()),
        _sequence_optional_component("salt", 1, KerberosString()),
        _sequence_optional_component("s2kparams", 2, univ.OctetString()),
    )

class PaDataEtypeInfo2(Asn1LeafMixin, univ.SequenceOf):
    componentType = PaDataEtypeInfo2Entry()


class PaData(univ.Sequence):
    """Kerberos PA Data ASN.1 representation"""

    componentType = namedtype.NamedTypes(
        _sequence_component("padata-type", 1, Int32()),
        _sequence_component("padata-value", 2, univ.OctetString()),
    )

class MethodData(Asn1LeafMixin, univ.SequenceOf):
    componentType = PaData()


class KerberosFlags(univ.BitString):
    """Kerberos flags ASN.1 representation"""


class EncryptedData(Asn1LeafMixin, univ.Sequence):
    componentType = namedtype.NamedTypes(
        _sequence_component("etype", 0, Int32()),
        _sequence_optional_component("kvno", 1, UInt32()),
        _sequence_component("cipher", 2, univ.OctetString()),
    )


class EncryptionKey(univ.Sequence):
    componentType = namedtype.NamedTypes(
        _sequence_component("keytype", 0, Int32()),
        _sequence_component("keyvalue", 1, univ.OctetString()),
    )


class Checksum(univ.Sequence):
    componentType = namedtype.NamedTypes(
        _sequence_component("cksumtype", 0, Int32()),
        _sequence_component("checksum", 1, univ.OctetString()),
    )


class Ticket(Asn1LeafMixin, univ.Sequence):
    tagSet = _application_tag(ApplicationTag.TICKET)
    componentType = namedtype.NamedTypes(
        _kvno_component("tkt-vno", 0),
        _sequence_component("realm", 1, Realm()),
        _sequence_component("sname", 2, PrincipalName()),
        _sequence_component("enc-part", 3, EncryptedData()),
    )


class TicketFlags(KerberosFlags):
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
        ("ok-as-delefate", 13),
    )


class TransitedEncoding(univ.Sequence):
    componentType = namedtype.NamedTypes(
        _sequence_component("tr-type", 0, Int32()),
        _sequence_component("contents", 1, univ.OctetString()),
    )


class EncTicketPart(univ.Sequence):
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


class KdcOptions(KerberosFlags):
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


class KdcReqBody(univ.Sequence):
    componentType = namedtype.NamedTypes(
        _sequence_component("kdc-options", 0, KdcOptions()),
        _sequence_component("cname", 1, PrincipalName()),
        _sequence_component("realm", 2, Realm()),
        _sequence_optional_component("sname", 3, PrincipalName()),
        _sequence_optional_component("from", 4, KerberosTime()),
        _sequence_component("till", 5, KerberosTime()),
        _sequence_optional_component("rtime", 6, KerberosTime()),
        _sequence_component("nonce", 7, UInt32()),
        _sequence_component("etype", 8, univ.SequenceOf(componentType=Int32())),
        _sequence_optional_component("addresses", 9, HostAddresses()),
        _sequence_optional_component("enc-authorization-data", 10, EncryptedData()),
        _sequence_optional_component("additional-tickets", 11, univ.SequenceOf(componentType=Ticket())),
    )


class KdcReq(univ.Sequence):
    componentType = namedtype.NamedTypes(
        _kvno_component("pvno", 1),
        _sequence_component(
            "msg-type",
            2,
            univ.Integer(),
            subtypeSpec=constraint.ConstraintsUnion(
                *(
                    constraint.SingleValueConstraint(v)
                    for v in [ApplicationTag.AS_REQ.value, ApplicationTag.TGS_REQ.value]
                )
            ),
        ),
        _sequence_optional_component("padata", 3, univ.SequenceOf(componentType=PaData())),
        _sequence_component("req-body", 4, KdcReqBody()),
    )

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
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
    tagSet = _application_tag(ApplicationTag.AS_REQ)


class TgsReq(KdcReq):
    tagSet = _application_tag(ApplicationTag.TGS_REQ)


class KdcRep(Asn1LeafMixin, univ.Sequence):
    componentType = namedtype.NamedTypes(
        _kvno_component("pvno", 0),
        _sequence_component(
            "msg-type",
            1,
            univ.Integer(),
            subtypeSpec=constraint.ConstraintsUnion(
                *(
                    constraint.SingleValueConstraint(v)
                    for v in [ApplicationTag.AS_REP.value, ApplicationTag.TGS_REP.value]
                )
            ),
        ),
        _sequence_optional_component("padata", 2, univ.SequenceOf(componentType=PaData())),
        _sequence_component("crealm", 3, Realm()),
        _sequence_component("cname", 4, PrincipalName()),
        _sequence_component("ticket", 5, Ticket()),
        _sequence_component("enc-part", 6, EncryptedData()),
    )


class AsRep(KdcRep):
    tagSet = _application_tag(ApplicationTag.AS_REP)


class TgsRep(KdcRep):
    tagSet = _application_tag(ApplicationTag.TGS_REP)


class EncKdcRepPart(Asn1LeafMixin, univ.Sequence):
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
    tagSet = _application_tag(ApplicationTag.ENC_AS_REP_PART)


class EncTgsRepPart(EncKdcRepPart):
    tagSet = _application_tag(ApplicationTag.ENC_TGS_REP_PART)


class KrbError(Asn1LeafMixin, univ.Sequence):
    tagSet = _application_tag(ApplicationTag.KRB_ERROR)
    componentType = namedtype.NamedTypes(
        _kvno_component("pvno", 0),
        _sequence_component(
            "msg-type",
            1,
            univ.Integer(),
            subtypeSpec=constraint.SingleValueConstraint(ApplicationTag.KRB_ERROR.value),
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


class KdcProxyMessage(Asn1LeafMixin, univ.Sequence):
    componentType = namedtype.NamedTypes(
        _sequence_component("message", 0, univ.OctetString()),
        _sequence_optional_component("target-domain", 1, Realm()),
        _sequence_optional_component("dclocator-hint", 2, univ.Integer()),
    )
