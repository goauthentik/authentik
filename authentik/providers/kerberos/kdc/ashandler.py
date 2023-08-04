from datetime import timedelta
from django.utils.timezone import now

from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.kerberos.kdc.kdcreqhandler import KdcReqMessageHandler
from authentik.providers.kerberos.kdc.preauth import PaBase
from authentik.providers.kerberos.lib import protocol, iana
from authentik.providers.kerberos.lib.exceptions import KerberosError, KerberosPreauthRequiredError


class PaEncTs(PaBase):
    PA_TYPE = iana.PreAuthenticationType.PA_ENC_TIMESTAMP
    context_attrs = ["ctime", "cusec"]

    def decrypt(self):
        self.paenctsenc = protocol.EncryptedData.from_bytes(self.padata_values[0]).to_python()

        enctype = self.paenctsenc["etype"][1]
        if enctype is None:
            raise KerberosError(code=KerberosError.Code.KDC_ERR_ETYPE_NOSUPP)

        self.key = self.parent.client.kerberoskeys.keys.get(enctype)
        if self.key is None:
            raise KerberosError(code=KerberosError.Code.KDC_ERR_NULL_KEY)

        try:
            self.paenctsenc.decrypt(
                self.key,
                protocol.KeyUsageNumbers.AS_REQ_PA_ENC_TIMESTAMP,
                protocol.PaDataEncTsEnc,
            )
        except ValueError:
            raise KerberosError(code=KerberosError.Code.KDC_ERR_PREAUTH_FAILED)

    def check(self) -> bool:
        if not super().check():
            return False

        self.decrypt()
        self.ctime = self.paenctsenc["plain"]["patimestamp"]
        self.cusec = self.paenctsenc["plain"].get("pausec", 0)
        timestamp = self.ctime + timedelta(microseconds=self.cusec)
        skew = timedelta_from_string(self.parent.service.maximum_skew)

        if not now() - skew < timestamp < now() + skew:
            raise KerberosError(code=KerberosError.Code.KDC_AP_ERR_SKEW)
        self.preauthenticated = True
        return True


class PaEtypeInfo2(PaBase):
    PA_TYPE = iana.PreAuthenticationType.PA_ETYPE_INFO2

    def build_padata(self) -> tuple[int, bytes]:
        enctype = self.parent.cenctype
        entries = []
        for etype, key in self.parent.client.kerberoskeys.keys.items():
            if enctype is None or etype == enctype:
                entries.append(
                    {
                        "etype": etype,
                        "salt": self.parent.client.kerberoskeys.salt,
                        "s2kparams": etype.s2k_params(),
                    }
                )
        if not entries:
            return None
        return (self.PA_TYPE.value, protocol.PaDataEtypeInfo2().from_python(entries).to_bytes())

    def check(self) -> bool:
        return False


class AsReqMessageHandler(KdcReqMessageHandler):
    MESSAGE_CLASS = protocol.AsReq
    RESPONSE_CLASS = protocol.AsRep
    RESPONSE_MSG_TYPE = protocol.ApplicationTag.AS_REP
    ENC_PART_CLASS = protocol.EncAsRepPart
    PREAUTH_IN_REP = (PaEtypeInfo2,)
    PREAUTH_CHECKS = (
        PaEncTs,
        PaEtypeInfo2,
    )

    def select_enctypes(self):
        super().select_enctypes()
        self.ckey = self.client.kerberoskeys.keys[self.cenctype]

    def fill_ticket(self):
        self.caddr = self.request["req-body"].get("addresses")
        super().fill_ticket()
        self.ticket["flags"]["initial"] = True

    def build_response(self):
        super().build_response()
        for Pa in self.PREAUTH_IN_REP:
            entry = Pa(self).build_padata()
            if entry is not None:
                self.response.setdefault("padata", []).append(entry)
        response = self.response

    def encrypt(self):
        super().encrypt()
        self.response["enc-part"].encrypt(
            key=self.ckey,
            usage=protocol.KeyUsageNumbers.AS_REP_ENCPART,
            asn1item=self.ENC_PART_CLASS(),
        )
