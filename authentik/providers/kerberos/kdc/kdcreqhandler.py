import secrets
from datetime import datetime
from typing import Self, Any

from django.utils.timezone import now
from django.views import View

from authentik.providers.kerberos.models import KerberosRealm
from authentik.providers.kerberos.kdc import checks
from authentik.providers.kerberos.lib.exceptions import KerberosError
from authentik.providers.kerberos.lib.iana import EncryptionType
from authentik.providers.kerberos.lib.protocol import (
    KdcReq,
    KdcRep,
    KrbError,
    KERBEROS_PVNO,
    KeyUsageNumbers,
    EncTicketPart,
    EncryptedDataWrapper,
    EncKdcRepPart,
)


class KdcReqMessageHandler:
    @classmethod
    def from_message(cls, view: View, message: bytes, **kwargs) -> Self:
        req = KdcReq.from_bytes(message)
        for subcls in cls.__subclasses__():
            if getattr(subcls, "MESSAGE_CLASS", None) is type(req):
                return subcls(view, req, req.to_python(), **kwargs)
        raise ValueError(f"No Message handler for {type(req)}")

    BEFORE_PREAUTH_CHECKS = (
        checks.PvnoCheck,
        checks.ServiceFromKdcReqCheck,
        checks.ServiceHasKeysCheck,
        checks.ClientRequestsKnownEnctypesCheck,
        checks.CnameFromKdcReqCheck,
        checks.ClientExistsCheck,
        checks.ClientHasKeysCheck,
    )

    PREAUTH_CHECKS = ()

    AFTER_PREAUTH_CHECKS = (
        checks.ProxiablePolicyCheck,
        checks.ForwardablePolicyCheck,
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
        for check in [cls(self) for cls in check_classes]:
            check.raise_if_failed()
            for fname, value in check.get_context().items():
                setattr(self, fname, value)

    def preauth(self):
        preauth_check = checks.PreauthRequiredCheck(self, checks=self.PREAUTH_CHECKS)
        preauth_check.raise_if_failed()
        for fname, value in preauth_check.get_context().items():
            setattr(self, fname, value)

    def select_enctypes(self):
        raise NotImplementedError

    def build_response(self):
        self.response.update(
            {
                "pvno": KERBEROS_PVNO,
                "msg-type": self.RESPONSE_MSG_TYPE.value,
                "crealm": self.realm.realm_name,
                "cname": self.client.username,
            }
        )

    def select_enctypes(self):
        svc_etypes = set(self.service.kerberoskeys.keys.keys())
        cl_etypes = set(self.client.kerberoskeys.keys.keys())
        skey_etypes = set(svc_etypes)

        if self.req_etypes:
            cl_etypes &= set(self.req_etypes)
            skey_etypes &= set(self.req_etypes)

        try:
            self.cenctype = max(cl_etypes, key=lambda e: e.ENC_TYPE.value)
            self.senctype = max(svc_etypes, key=lambda e: e.ENC_TYPE.value)
            self.skey_enctype = max(skey_etypes, key=lambda e: e.ENC_TYPE.value)
        except ValueError as exc:
            raise KerberosError(code=KerberosError.Code.KDC_ERR_NULL_KEY) from exc

    def set_times(self):
        self.authtime = now()
        self.starttime = self.request["req-body"].get("from")
        self.endtime = self.request["req-body"].get("till")
        self.renew_till = self.request["req-body"].get("rtime")

    def fill_ticket(self):
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
        if hasattr(self, "preauthenticated"):
            self.ticket["flags"]["pre-authent"] = self.preauthenticated

    def fill_encpart(self):
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

    def encrypt(self):
        self.response["ticket"]["enc-part"].encrypt(
            key=self.service.kerberoskeys.keys[self.senctype],
            usage=KeyUsageNumbers.KDC_REP_TICKET,
            asn1item=EncTicketPart(),
        )

    def handle(self) -> KdcRep | KrbError:
        try:
            self.check(self.BEFORE_PREAUTH_CHECKS)
            self.preauth()
            self.check(self.AFTER_PREAUTH_CHECKS)
            self.select_enctypes()
            self.set_times()
            self.fill_ticket()
            self.fill_encpart()
            self.encrypt()
            self.build_response()
            return self.RESPONSE_CLASS().from_python(self.response)
        except KerberosError as exc:
            return exc.to_krberror(handler=self)
