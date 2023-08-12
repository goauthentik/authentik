from typing import Any, Self

from django.views import View

from authentik.providers.kerberos.kdc import checks
from authentik.providers.kerberos.lib.exceptions import KerberosError
from authentik.providers.kerberos.lib.protocol import (
    KERBEROS_PVNO,
    ApplicationTag,
    AsRep,
    AsReq,
    EncAsRepPart,
    EncKdcRepPart,
    EncryptedDataWrapper,
    EncTgsRepPart,
    EncTicketPart,
    KdcRep,
    KdcReq,
    KeyUsageNumbers,
    KrbError,
    TgsRep,
    TgsReq,
)
from authentik.providers.kerberos.models import KerberosRealm


class KdcReqMessageHandler:
    """Base KDC request handler"""

    @classmethod
    def from_message(cls, view: View, message: bytes, **kwargs) -> Self:
        """Create a handler from a message. Chooses the correct handler depending on the message type."""
        req = KdcReq.from_bytes(message)
        for subcls in cls.__subclasses__():
            if getattr(subcls, "MESSAGE_CLASS", None) is type(req):
                return subcls(view, req, req.to_python(), **kwargs)
        raise ValueError(f"No Message handler for {type(req)}")

    MESSAGE_CLASS: KdcReq
    RESPONSE_CLASS: KdcRep
    RESPONSE_MSG_TYPE: ApplicationTag
    RESPONSE_ENCPART_KEY_USAGE: KeyUsageNumbers
    ENC_PART_CLASS: EncKdcRepPart
    PREAUTH_IN_REP: tuple[checks.Check] = ()
    PREAUTH_CHECKS: tuple[checks.Check] = ()

    BEFORE_PREAUTH_CHECKS: tuple[checks.Check] = (
        checks.PvnoCheck,
        checks.ServiceFromKdcReqCheck,
        checks.ServiceHasKeysCheck,
        checks.ClientRequestsKnownEnctypesCheck,
        checks.CnameFromKdcReqCheck,
        checks.ClientExistsCheck,
        checks.ClientHasKeysCheck,
    )

    PREAUTH_CHECKS: tuple[checks.Check] = ()

    AFTER_PREAUTH_CHECKS: tuple[checks.Check] = (
        checks.ProxiablePolicyCheck,
        checks.ForwardablePolicyCheck,
        checks.PostdatePolicyCheck,
        checks.RenewablePolicyCheck,
        checks.StarttimeCheck,
        checks.EndtimeCheck,
        checks.RenewableCheck,
        checks.NeverValidCheck,
    )

    def __init__(self, view: View, message: KdcReq, request: dict[str, Any], realm: KerberosRealm):
        self.view = view
        self.request = request
        self.message = message
        self.realm = realm
        self.client = None
        self.cenctype = None
        self.service = None
        self.senctype = None
        self.skey_enctype = None
        self.response = {}
        self.ticket = {}
        self.starttime = None
        self.endtime = None
        self.renew_till = None
        self.caddr = None
        self.flags = {}

    def check(self, check_classes):
        for check in (cls(self) for cls in check_classes):
            check.raise_if_failed()
            for fname, value in check.get_context().items():
                setattr(self, fname, value)

    def preauth(self):
        preauth_check = checks.PreauthRequiredCheck(self, checks=self.PREAUTH_CHECKS)
        preauth_check.raise_if_failed()
        for fname, value in preauth_check.get_context().items():
            setattr(self, fname, value)

    def select_enctypes(self):
        svc_etypes = set(self.service.kerberoskeys.keys.keys())
        cl_etypes = set(self.client.kerberoskeys.keys.keys())
        skey_etypes = set(svc_etypes)

        if self.req_etypes:
            cl_etypes &= set(self.req_etypes)
            skey_etypes &= set(self.req_etypes)

        # TODO: use IntEnum
        try:
            self.cenctype = max(cl_etypes, key=lambda e: e.ENC_TYPE)
            self.senctype = max(svc_etypes, key=lambda e: e.ENC_TYPE)
            self.skey_enctype = max(skey_etypes, key=lambda e: e.ENC_TYPE)
        except ValueError as exc:
            raise KerberosError(code=KerberosError.Code.KDC_ERR_NULL_KEY) from exc

    def fill_response_ticket(self):
        ticket = self.response.setdefault("ticket", {})
        ticket.update(
            {
                "tkt-vno": KERBEROS_PVNO,
                "realm": self.realm.realm_name,
                "sname": self.service.spn,
                "enc-part": EncryptedDataWrapper(),
            }
        )
        self.ticket.update(
            {
                "flags": self.flags,
                "key": {
                    "keytype": self.skey_enctype,
                    "keyvalue": self.skey_enctype.generate_key(),
                },
                "crealm": self.realm.realm_name,
                "cname": self.client.username,
                "transited": {
                    "tr-type": 1,
                    "contents": "".encode(),
                },
                "authtime": self.authtime,
                "starttime": self.starttime,
                "endtime": self.endtime,
                "renew-till": self.renew_till,
                "caddr": self.caddr,
            }
        )
        ticket["enc-part"].update(
            {
                "etype": self.senctype,
                "kvno": self.service.kerberoskeys.kvno,
                "plain": self.ticket,
            }
        )
        self.ticket["flags"]["renewable"] = self.renewable
        self.ticket["flags"]["proxiable"] = self.request["req-body"]["kdc-options"]["proxiable"]
        self.ticket["flags"]["forwardable"] = self.request["req-body"]["kdc-options"]["forwardable"]
        self.ticket["flags"]["ok-as-delegate"] = self.service.set_ok_as_delegate
        self.ticket["flags"]["may-postdate"] = self.request["req-body"]["kdc-options"][
            "allow-postdate"
        ]
        self.ticket["flags"]["postdated"] = self.postdated
        self.ticket["flags"]["invalid"] = self.postdated
        self.ticket["flags"]["pre-authent"] = getattr(self, "preauthenticated", False)

    def fill_response_encpart(self):
        encpart = self.response.setdefault("enc-part", EncryptedDataWrapper())
        encpart.setdefault("plain", {})
        encpart.setdefault("etype", self.cenctype)
        encpart.setdefault("kvno", self.client.kerberoskeys.kvno)

        encpart["plain"].update(
            {
                "nonce": self.request["req-body"]["nonce"],
                "last-req": [],
                "srealm": self.response["ticket"]["realm"],
                "sname": self.response["ticket"]["sname"],
            }
        )

        for key in ("flags", "key", "authtime", "starttime", "endtime", "renew-till", "caddr"):
            if key in self.ticket:
                encpart["plain"][key] = self.ticket[key]

    def get_response_encpart_key_usage(self):
        return self.RESPONSE_ENCPART_KEY_USAGE

    def get_response_encpart_key(self):
        return self.ckey

    def encrypt_response(self):
        self.response["ticket"]["enc-part"].encrypt(
            key=self.service.kerberoskeys.keys[self.senctype],
            usage=KeyUsageNumbers.KDC_REP_TICKET,
            asn1item=EncTicketPart(),
        )
        self.response["enc-part"].encrypt(
            key=self.ckey,
            usage=self.get_response_encpart_key_usage(),
            asn1item=self.ENC_PART_CLASS(),
        )

    def build_response(self):
        self.response.update(
            {
                "pvno": KERBEROS_PVNO,
                "msg-type": self.RESPONSE_MSG_TYPE,
                "crealm": self.realm.realm_name,
                "cname": self.client.username,
            }
        )
        for Pa in self.PREAUTH_IN_REP:
            entry = Pa(self).build_padata()
            if entry is not None:
                self.response.setdefault("padata", []).append(entry)

    def handle(self) -> KdcRep | KrbError:
        try:
            self.check(self.BEFORE_PREAUTH_CHECKS)
            self.preauth()
            self.check(self.AFTER_PREAUTH_CHECKS)
            self.select_enctypes()
            self.fill_response_ticket()
            self.fill_response_encpart()
            self.encrypt_response()
            self.finalize_response()
            return self.RESPONSE_CLASS().from_python(self.response)
        except KerberosError as exc:
            return exc.to_krberror(handler=self)


class AsReqMessageHandler(KdcReqMessageHandler):
    MESSAGE_CLASS = AsReq
    RESPONSE_CLASS = AsRep
    RESPONSE_MSG_TYPE = ApplicationTag.AS_REP
    RESPONSE_ENCPART_KEY_USAGE = KeyUsageNumbers.AS_REP_ENCPART
    ENC_PART_CLASS = EncAsRepPart
    PREAUTH_IN_REP = (checks.PaEtypeInfo2,)

    BEFORE_PREAUTH_CHECKS = KdcReqMessageHandler.BEFORE_PREAUTH_CHECKS + (
        checks.CnameFromKdcReqCheck,
        checks.ClientExistsCheck,
        checks.ClientHasKeysCheck,
    )
    PREAUTH_CHECKS = (
        checks.PaEncTs,
        checks.PaEtypeInfo2,
    )

    def select_enctypes(self):
        super().select_enctypes()
        self.ckey = self.client.kerberoskeys.keys[self.cenctype]

    def fill_response_ticket(self):
        self.caddr = self.request["req-body"].get("addresses")
        super().fill_ticket()
        self.ticket["flags"]["initial"] = True


class TgsReqMessageHandler(KdcReqMessageHandler):
    MESSAGE_CLASS = TgsReq
    RESPONSE_CLASS = TgsRep
    RESPONSE_MSG_TYPE = ApplicationTag.TGS_REP
    ENC_PART_CLASS = EncTgsRepPart

    PREAUTH_CHECKS = (checks.PaTgsReq,)

    AFTER_PREAUTH_CHECKS = (
        checks.ApReqTicketInvalidCheck,
        checks.ApReqTicketExpiredCheck,
        checks.ApReqPreAuthentFlag,
        checks.ApReqTicketMayPostdateCheck,
        checks.ApReqTicketAllowPostdateCheck,
        checks.ApReqTicketRenewableCheck,
        checks.ProxiableOptionCheck,
        checks.ForwardableOptionCheck,
        checks.ProxiablePolicyCheck,
        checks.ForwardablePolicyCheck,
        checks.PostdatePolicyCheck,
        checks.RenewablePolicyCheck,
        checks.StarttimeCheck,
        checks.EndtimeCheck,
        checks.ApReqTicketEndtimeCheck,
        checks.RenewableCheck,
        checks.NeverValidCheck,
    )

    def select_enctypes(self):
        super().select_enctypes()
        self.ckey = self.subkey or self.ap_req["ticket"]["enc-part"]["plain"]["key"]["keyvalue"]
        self.cenctype = (
            self.subkey_enctype or self.ap_req["ticket"]["enc-part"]["plain"]["key"]["etype"][1]
        )

    def get_response_encpart_key_usage(self):
        if self.subkey:
            return KeyUsageNumbers.TGS_REP_ENCPART_AUTHENTICATOR_SUB_KEY
        return KeyUsageNumbers.TGS_REP_ENCPART_SESSION_KEY

    def get_response_encpart_key(self):
        return self.subkey or self.ckey
