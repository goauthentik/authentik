from datetime import timedelta, timedelta
from typing import Any
from django.utils.timezone import now

from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.kerberos.kdc.kdcreqhandler import KdcReqMessageHandler
from authentik.providers.kerberos.kdc.preauth import PaBase
from authentik.providers.kerberos.kdc import checks
from authentik.providers.kerberos.lib import protocol, iana, crypto
from authentik.providers.kerberos.lib.exceptions import KerberosError, KerberosPreauthRequiredError
from authentik.providers.kerberos import models


class ApReqPvnoCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_BADVERSION

    def check(self) -> bool:
        return self.parent.request["pvno"] == protocol.KERBEROS_PVNO


class ApReqMsgTypeCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_MSG_TYPE

    def check(self) -> bool:
        return self.parent.request["msg-type"] == protocol.ApplicationTag.AP_REQ.value


class CnameFromApReqCheck(checks.Check):
    context_attrs = ["cname", "crealm"]

    def check(self) -> bool:
        self.cname = self.parent.request["ticket"]["enc-part"]["plain"]["cname"]
        self.crealm = self.parent.request["ticket"]["enc-part"]["plain"]["crealm"]
        return True


class ServiceFromApReqCheck(checks.Check):
    error_code = KerberosError.Code.KDC_ERR_S_PRINCIPAL_UNKNOWN
    context_attrs = ["service", "srealm"]

    def check(self) -> bool:
        self.srealm = self.parent.ap_req["ticket"]["realm"]
        self.service = models.KerberosProvider.objects.filter(
            spn=self.parent.request["ticket"]["sname"],
            realms__realm_name=self.srealm,
        ).first()
        return self.service is not None


class AuthenticatorEnctypeIsSupportedCheck(checks.Check):
    error_code = KerberosError.Code.KDC_ERR_ETYPE_NOSUPP

    def check(self) -> bool:
        return self.parent.request["ticket"]["enc-part"]["etype"][1] is not None


class ApReqServiceHasKeysCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_NOKEY

    def check(self) -> bool:
        enctype = self.parent.request["ticket"]["enc-part"]["etype"][1]
        return (
            hasattr(self.parent.service, "kerberoskeys")
            and enctype in self.parent.service.kerberoskeys.keys
        )


class ApReqServiceKeysKvnoCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_BADKEYVER

    def check(self) -> bool:
        kvno = self.parent.request["ticket"]["enc-part"].get("kvno")
        return kvno is not None and self.parent.service.kerberoskeys.kvno == kvno


class UserToUserCheck(checks.Check):
    error_message = "user-to-user is not supported by this KDC implementation"

    def check(self) -> bool:
        return not self.parent.request["ap-options"]["use-session-key"]


class TicketIntegrityCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_BAD_INTEGRITY

    def check(self) -> bool:
        enctype = self.parent.request["ticket"]["enc-part"]["etype"][1]
        try:
            self.parent.request["ticket"]["enc-part"].decrypt(
                key=self.parent.service.kerberoskeys.keys[enctype],
                usage=protocol.KeyUsageNumbers.KDC_REP_TICKET,
                plain_cls=protocol.EncTicketPart(),
            )
        except ValueError:
            return False
        return True

class ServiceMatchCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_NOT_US

    def check(self) -> bool:
        if self.parent.service.is_tgs:
            return True
        if self.parent.service != self.parent.parent.service:
            return False
        options = self.parent.parent.request["req-body"]["kdc-options"]
        return options["renew"] or options["validate"] or options["proxy"]


class SkeyEnctypeCheck(checks.Check):
    error_code = KerberosError.Code.KDC_ERR_ETYPE_NOSUPP
    context_attrs = ["skey", "skey_enctype"]

    def check(self) -> bool:
        self.skey = self.parent.request["ticket"]["enc-part"]["plain"]["key"]["keyvalue"]
        self.skey_enctype = self.parent.request["ticket"]["enc-part"]["plain"]["key"]["keytype"][1]
        return self.skey_enctype is not None


class AuthenticatorIntegrityCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_BAD_INTEGRITY

    def check(self) -> bool:
        enctype = self.parent.request["authenticator"]["etype"][1]
        if enctype != self.parent.skey_enctype:
            return False
        try:
            self.parent.request["authenticator"].decrypt(
                key=self.parent.skey,
                usage=protocol.KeyUsageNumbers.TGS_REQ_PA_TGS_REQ_AP_REQ_AUTHENTICATOR,
                plain_cls=protocol.Authenticator(),
            )
        except ValueError:
            return False
        return True


class AuthenticatorVnoCheck(checks.Check):
    error_code = KerberosError.Code.KDC_ERR_BAD_PVNO

    def check(self) -> bool:
        return (
            self.parent.request["authenticator"]["plain"]["authenticator-vno"]
            == protocol.KERBEROS_PVNO
        )


class AuthenticatorMatchCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_BADMATCH

    def check(self) -> bool:
        return all(
            [
                self.parent.request["authenticator"]["plain"]["cname"] == self.parent.cname,
                self.parent.request["authenticator"]["plain"]["crealm"] == self.parent.crealm,
            ]
        )


class CaddrCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_BADADDR

    def check(self) -> bool:
        if self.parent.request["ticket"]["enc-part"]["plain"].get("caddr") is not None:
            for addr_type, addr in self.parent.request["ticket"]["enc-part"]["plain"]["caddr"]:
                if addr == self.parent.parent.view.remote_addr:
                    return True
            return False
        return True


class AuthenticatorValidityCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_SKEW
    context_attrs = ["ctime", "cusec"]

    def check(self) -> bool:
        self.ctime = self.parent.request["authenticator"]["plain"]["ctime"]
        self.cusec = self.parent.request["authenticator"]["plain"]["cusec"]
        timestamp = self.ctime + timedelta(microseconds=self.cusec)
        skew = timedelta_from_string(self.parent.service.maximum_skew)
        return now() - skew < timestamp < now() + skew


class AuthenticatorCksumExistsCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_INAPP_CKSUM
    context_attrs = ["cksum"]

    def check(self) -> bool:
        if "cksum" not in self.parent.request["authenticator"]["plain"]:
            return False
        self.cksum = self.parent.request["authenticator"]["plain"]["cksum"]["checksum"]
        return True


class AuthenticatorCksumTypeSupportedCheck(checks.Check):
    error_code = KerberosError.Code.KDC_ERR_SUMTYPE_NOSUPP
    context_attrs = ["cksumtype"]

    def check(self) -> bool:
        try:
            self.cksumtype = crypto.get_checksumtype_from_value(
                self.parent.request["authenticator"]["plain"]["cksum"]["cksumtype"]
            )
        except IndexError:
            return False
        return True


class AuthenticatorCksumCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_MODIFIED

    def check(self) -> bool:
        req_body = self.parent.parent.message["req-body"].to_bytes()

        # Skip tag and size in DER encoded bytestring
        if req_body[1] & 0x80:
            size_field_length = 1 + (req_body[1] & 0x7F)
        else:
            size_field_length = 1

        return self.parent.cksumtype.verify_checksum(
            key=self.parent.skey,
            data=req_body[1+size_field_length:],
            checksum=self.parent.cksum,
            usage=protocol.KeyUsageNumbers.TGS_REQ_PA_TGS_REQ_AP_REQ_AUTHENTICATOR_CHKSUM.value,
        )


class AuthenticatorSubkeyEnctypeIsSupportedCheck(checks.Check):
    error_code = KerberosError.Code.KDC_ERR_ETYPE_NOSUPP
    context_attrs = ["subkey", "subkey_enctype"]

    def check(self) -> bool:
        if not "subkey" in self.parent.request["authenticator"]["plain"]:
            self.subkey = None
            self.subkey_enctype = None
            return True
        self.subkey = self.parent.request["authenticator"]["plain"]["subkey"]["keyvalue"]
        self.subkey_enctype = self.parent.request["authenticator"]["plain"]["subkey"]["keytype"][1]
        return self.subkey_enctype is not None


class ForwardableOptionCheck(checks.Check):
    error_code: int = KerberosError.Code.KDC_ERR_BADOPTION

    def check(self):
        if not self.parent.request["req-body"]["kdc-options"]["forwardable"]:
            return True
        return self.parent.ap_req["ticket"]["enc-part"]["plain"]["flags"]["forwardable"]


class ProxiableOptionCheck(checks.Check):
    error_code: int = KerberosError.Code.KDC_ERR_BADOPTION

    def check(self):
        if not self.parent.request["req-body"]["kdc-options"]["proxiable"]:
            return True
        if not self.parent.ap_req["ticket"]["enc-part"]["plain"]["flags"]["proxiable"]:
            return False
        return not self.parent.service.is_tgs


class PaTgsReq(PaBase, checks.Checks):
    PA_TYPE = iana.PreAuthenticationType.PA_TGS_REQ
    error_code = KerberosError.Code.KDC_ERR_PADATA_TYPE_NOSUPP
    context_attrs = [
        "ap_req",
        "client",
        "crealm",
        "srealm",
        "ap_req_service",
        "ctime",
        "cusec",
        "skey",
        "skey_enctype",
        "subkey",
        "subkey_enctype",
    ]

    checks = (
        checks.PvnoCheck,
        UserToUserCheck,
        ApReqMsgTypeCheck,
        ServiceFromApReqCheck,
        AuthenticatorEnctypeIsSupportedCheck,
        ApReqServiceHasKeysCheck,
        ApReqServiceKeysKvnoCheck,
        TicketIntegrityCheck,
        CnameFromApReqCheck,
        checks.ClientExistsCheck,
        SkeyEnctypeCheck,
        AuthenticatorIntegrityCheck,
        AuthenticatorMatchCheck,
        CaddrCheck,
        ServiceMatchCheck,
        AuthenticatorValidityCheck,
        AuthenticatorCksumExistsCheck,
        AuthenticatorCksumTypeSupportedCheck,
        AuthenticatorCksumCheck,
        AuthenticatorSubkeyEnctypeIsSupportedCheck,
    )

    def get_checks_kwargs(self) -> dict[str, Any]:
        return {"parent": self}

    def check(self) -> bool:
        if not super().check():
            return False

        self.ap_req = self.request = protocol.ApReq.from_bytes(self.padata_values[0]).to_python()
        self.check_all()
        self.ap_req_service = self.service
        return True


class ApReqPreAuthentFlag(checks.Check):
    context_attrs = ["preauthenticated"]

    def check(self) -> bool:
        self.preauthenticated = self.parent.ap_req["ticket"]["enc-part"]["plain"]["flags"].get(
            "pre-authent", False
        )
        return True

class ApReqTicketInvalidCheck(checks.Check):
    error_code = KerberosError.Code.KRB_AP_ERR_TKT_NYV

    def check(self) -> bool:
        if not self.parent.ap_req["ticket"]["enc-part"]["plain"]["flags"]["invalid"]:
            return True
        return self.parent.parent.request["req-body"]["kdc-options"]["validate"]

class ApReqTicketMayPostdateCheck(checks.Check):
    error_code = KerberosError.Code.KDC_ERR_BADOPTION

    def check(self) -> bool:
        if not self.parent.ap_req["ticket"]["enc-part"]["plain"]["flags"]["may-postdate"]:
            return True
        return not self.parent.parent.request["req-body"]["kdc-options"]["postdated"]

class ApReqTicketAllowPostdateCheck(checks.Check):
    error_code = KerberosError.Code.KDC_ERR_BADOPTION

    def check(self) -> bool:
        if not self.parent.ap_req["ticket"]["enc-part"]["plain"]["flags"]["may-postdate"]:
            return True
        return not self.parent.parent.request["req-body"]["kdc-options"]["allow-postdate"]


class TgsReqMessageHandler(KdcReqMessageHandler):
    MESSAGE_CLASS = protocol.TgsReq
    RESPONSE_CLASS = protocol.TgsRep
    RESPONSE_MSG_TYPE = protocol.ApplicationTag.TGS_REP
    ENC_PART_CLASS = protocol.EncTgsRepPart
    PREAUTH_IN_REP = ()

    BEFORE_PREAUTH_CHECKS = (
        checks.PvnoCheck,
        checks.ServiceFromKdcReqCheck,
        checks.ServiceHasKeysCheck,
        checks.ClientRequestsKnownEnctypesCheck,
    )

    PREAUTH_CHECKS = (PaTgsReq,)

    AFTER_PREAUTH_CHECKS = (
        ApReqTicketInvalidCheck,
        ApReqPreAuthentFlag,
        ApReqTicketMayPostdateCheck,
        ApReqTicketAllowPostdateCheck,
        ProxiableOptionCheck,
        ForwardableOptionCheck,
        checks.ProxiablePolicyCheck,
        checks.ForwardablePolicyCheck,
    )

    def select_enctypes(self):
        super().select_enctypes()
        self.ckey = self.subkey or self.ap_req["ticket"]["enc-part"]["plain"]["key"]["keyvalue"]
        self.cenctype = (
            self.subkey_enctype or self.ap_req["ticket"]["enc-part"]["plain"]["key"]["etype"][1]
        )

    def encrypt(self):
        super().encrypt()
        if self.subkey:
            usage = protocol.KeyUsageNumbers.TGS_REP_ENCPART_AUTHENTICATOR_SUB_KEY
        else:
            usage = protocol.KeyUsageNumbers.TGS_REP_ENCPART_SESSION_KEY
        self.response["enc-part"].encrypt(
            key=self.ckey,
            usage=usage,
            asn1item=self.ENC_PART_CLASS(),
        )
