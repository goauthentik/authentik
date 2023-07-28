"""authentik Kerberos views"""
from dataclasses import dataclass, field
from base64 import b64decode
from datetime import timedelta

from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import SuspiciousOperation
from structlog.stdlib import get_logger

from authentik.lib.kerberos import crypto, iana
from authentik.lib.kerberos.exceptions import KerberosError
from authentik.lib.kerberos.protocol import (
    AsRep,
    AsReq,
    KdcProxyMessage,
    KdcRep,
    KdcReq,
    KrbError,
    KeyUsageNumbers,
    PaData,
    TgsRep,
    TgsReq,
    EncryptedData,
    PaDataEncTsEnc,
    PaDataEtypeInfo2,
    PaDataEtypeInfo2Entry,
    ApplicationTag,
    PrincipalNameType,
    PrincipalName,
    MethodData,
)
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.kerberos.models import KerberosProvider, KerberosRealm
from authentik.core.models import User

LOGGER = get_logger()


@dataclass
class Context:
    request: HttpRequest
    message: KdcReq
    realm: KerberosRealm | None = None
    user: User | None = None
    cname: PrincipalName | None = None
    sname: PrincipalName | None = None
    provider: KerberosProvider | None = None
    pa_data: MethodData = field(default_factory=MethodData)
    encrypted_part_key: bytes | None = None
    encrypted_part_enctype: crypto.EncryptionType | None = None
    client_authority: iana.PreAuthenticationType | None = None

    @property
    def preauth_satisfied(self) -> bool:
        return self.encrypted_part_key is not None

    def __post_init__(self):
        self.realm = KerberosRealm(name=self.message["req-body"]["realm"])
        self.sname = self.message["req-body"]["sname"]
        self.cname = self.message["req-body"]["cname"]


class PaHandler:
    PRE_AUTHENTICATION_TYPE: iana.PreAuthenticationType

    def __init__(self, ctx: Context):
        self.ctx = ctx

    def pre_validate(self):
        pass

    def validate(self):
        pass

    def post_validate(self):
        pass


class PaEtypeInfo2(PaHandler):
    PRE_AUTHENTICATION_TYPE = iana.PreAuthenticationType.PA_ETYPE_INFO2

    def post_validate(self):
        if not self.ctx.user:
            return

        entries = PaDataEtypeInfo2()
        if self.ctx.encrypted_part_enctype:
            entry = PaDataEtypeInfo2Entry()
            entry["etype"] = self.ctx.encrypted_part_enctype.value
            entry["salt"] = str(self.ctx.user.uuid).encode("utf-8")
            entry["s2kparams"] = self.ctx.encrypted_part_enctype.s2k_params()
        else:
            for enctype_value in map(int, self.ctx.user.krb5_keys.keys()):
                entry = PaDataEtypeInfo2Entry()
                entry["etype"] = enctype_value
                entry["salt"] = str(self.ctx.user.uuid).encode("utf-8")
                entry["s2kparams"] = crypto.get_enctype_from_value(enctype_value).s2k_params()
                entries.append(entry)

        padata = PaData()
        padata["padata-type"] = self.PRE_AUTHENTICATION_TYPE.value
        padata["padata-value"] = entries.to_bytes()
        self.ctx.pa_data.append(padata)


class PaEncTimestampHandler(PaHandler):
    PRE_AUTHENTICATION_TYPE = iana.PreAuthenticationType.PA_ENC_TIMESTAMP

    def _get_padata_timestamp(self):
        for padata in self.ctx.message.getComponentByName("padata", []):
            if padata["padata-type"] != iana.PreAuthenticationType.PA_ENC_TIMESTAMP.value:
                continue
            return padata
        return None

    def _check_padata_timestamp(self, paenctsenc: PaDataEncTsEnc) -> bool:
        patimestamp = paenctsenc["patimestamp"]
        pausec = paenctsenc.getComponentByName("pausec", 0)
        dt = patimestamp.asDateTime() + timedelta(microseconds=pausec)
        target_entity = self.ctx.provider or self.ctx.realm
        skew = timedelta_from_string(target_entity.maximum_skew)
        return now() - skew < dt < now() + skew

    def validate(self):
        if self.ctx.preauth_satisfied:
            return

        padata = self._get_padata_timestamp()

        if padata is None:
            padata = PaData()
            padata["padata-type"] = self.PRE_AUTHENTICATION_TYPE.value
            padata["padata-value"] = bytes()
            self.ctx.pa_data.append(padata)
            return

        encdata = EncryptedData.from_bytes(padata["padata-value"])
        enctype_value = encdata["etype"]

        try:
            enctype = crypto.get_enctype_from_value(enctype_value)
        except IndexError as exc:
            raise KerberosError(code=KerberosError.Code.KDC_ERR_ETYPE_NOSUPP) from exc

        try:
            key = b64decode(self.ctx.user.krb5_keys[str(enctype_value)].encode())
        except IndexError as exc:
            raise KerberosError(code=KerberosError.Code.KDC_ERR_ETYPE_NOSUPP) from exc

        paenctsenc = PaDataEncTsEnc.from_bytes(
            enctype.decrypt_message(
                key=key,
                ciphertext=bytes(encdata["cipher"]),
                usage=KeyUsageNumbers.AS_REQ_PA_ENC_TIMESTAMP.value,
            )
        )

        if not self._check_padata_timestamp(self, paenctsenc):
            raise KerberosError(code=KerberosError.Code.KDC_ERR_PREAUTH_FAILED)

        self.ctx.encrypted_part_key = key
        self.ctx.encrypted_part_enctype = enctype
        self.ctx.client_authority = self.PRE_AUTHENTICATION_TYPE


class MessageHandler:
    PA_HANDLERS: list[PaHandler]

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.pa_handlers = [handler(ctx) for handler in self.PA_HANDLERS]

    def pre_validate(self) -> KrbError:
        for handler in self.pa_handlers:
            handler.pre_validate()

    def query_pre_validate(self):
        raise NotImplementedError

    def process_pre_auth(self):
        for handler in self.pa_handlers:
            handler.validate()

    def post_validate(self) -> KrbError:
        for handler in self.pa_handlers:
            handler.post_validate()

    def validate_ticket_request(self):
        pass

    def query_pre_execute(self):
        pass

    def execute(self):
        raise NotImplementedError

    def handle(self) -> KdcRep | KrbError:
        try:
            if self.ctx.message["pvno"] != 5: # TODO: make constant
                raise KerberosError(code=KerberosError.Code.KDC_ERR_BAD_PVNO)
            self.pre_validate()
            self.query_pre_validate()
            self.process_pre_auth()
            self.post_validate()
            self.validate_ticket_request()
            self.query_pre_execute()
            return self.execute()
        except KerberosError as exc:
            return exc.to_krberror(
                realm=self.ctx.realm.name,
                crealm=self.ctx.realm.name, # TODO: use crealm
                cname=self.ctx.cname,
                sname=self.ctx.sname,
            )


class AsMessageHandler(MessageHandler):
    PA_HANDLERS = [
        PaEncTimestampHandler,
        PaEtypeInfo2,
    ]

    def execute(self) -> KdcRep | KrbError:
        if not self.ctx.preauth_satisfied:
            raise KerberosError(
                code=KerberosError.Code.KDC_ERR_PREAUTH_REQUIRED,
                context={
                    "e-data": self.ctx.pa_data.to_bytes(),
                },
            )

        enc_ticket_part = EncTicketPart()
        enc_ticket_part["flags"] = 0 # TODO: flags
        enc_ticket_part["key"] = None # TODO: session key
        enc_ticket_part["crealm"] = self.ctx.realm.name
        enc_ticket_part["cname"] = self.ctx.cname
        enc_ticket_part["transited"] = [] # TODO
        enc_ticket_part["authtime"] = now() # TODO: handle renew
        enc_ticket_part["starttime"] = now() # TODO: handle postdated
        enc_ticket_part["endtime"] = self.ctx.message["req-body"]["till"] # TODO: bound, time in the past, after from
        #enc_ticket_part["renew-till"] = now() # TODO

        if "addresses" in self.ctx.message["req-body"]:
            enc_ticket_part["caddr"] = self.ctx.message["req-body"]["addresses"]
        if "authorization-data" in self.ctx.message["req-body"]:
            enc_ticket_part["caddr"] = self.ctx.message["req-body"]["authorization-data"]


        ticket = Ticket()
        ticket["tkt-vno"] = 5 # make constant
        ticket["realm"] = self.ctx.realm.name
        ticket["sname"] = self.ctx.sname
        ticket["enc-part"] = self.ctx.encrypted_part_enctype.encrypt_data(
            self.ctx.realm.keys[self.ctx.encrypted_part_enctype],
            enc_ticket_part.to_bytes(),
        )

        enc_as_rep_part = EncAsRepPart()
        enc_as_rep_part["last-req"] = []
        enc_as_rep_part["nonce"] = self.ctx.message["req-body"]["nonce"]
        enc_as_rep_part["srealm"] = self.ctx.realm.name
        enc_as_rep_part["sname"] = self.ctx.sname
        for k in ("flags", "authtime", "starttime", "endtime", "renew-till",
                  "caddr", "key"):
            enc_as_rep_part[k] = enc_ticket_part[k]


        rep = AsRep()
        rep["pvno"] = 5 # TODO: make constant
        rep["msg-type"] = ApplicationTag.AS_REP.value
        if self.ctx.pa_data:
            rep["padata"] = self.ctx.padata
        rep["crealm"] = self.ctx.realm.name
        rep["cname"] = self.ctx.cname
        rep["ticket"] = ticket
        rep["enc-part"] = self.ctx.encrypted_part_enctype.encrypt_data(
            self.ctx.encrypted_part_key,
            enc_as_rep_part.to_bytes(),
        )

        return rep

    def query_pre_validate(self):
        self.ctx.realm = KerberosRealm.objects.filter(
            name=self.ctx.message["req-body"]["realm"]
        ).first()
        if not self.ctx.realm:
            raise KerberosError("realm not found")

        self.ctx.user = User.objects.filter(
            username=self.ctx.message["req-body"]["cname"].to_string(),
        ).first()
        if not self.ctx.user:
            raise KerberosError(code=KerberosError.Code.KDC_ERR_C_PRINCIPAL_UNKNOWN)

        tgs_name = PrincipalName.from_components(
            name_type=PrincipalNameType.NT_SRV_INST,
            name=["krbtgt", self.ctx.realm.name],
        )
        if self.ctx.sname != tgs_name:
            self.ctx.provider = KerberosProvider.objects.filter(
                service_principal_name=self.ctx.message["req-body"]["sname"].to_string()
            ).first()
            if not self.ctx.provider:
                raise KerberosError(code=KerberosError.Code.KDC_ERR_S_PRINCIPAL_UNKNOWN)


    def query_pre_execute(self):
        # TODO: check flags and policy
        pass


@method_decorator(csrf_exempt, name="dispatch")
class KdcProxyView(View):
    def post(self, request: HttpRequest, **kwargs) -> HttpResponse:
        try:
            proxy_message = KdcProxyMessage.from_bytes(request.body)
            expected_length = int.from_bytes(proxy_message["message"][:4])
            real_length = len(proxy_message["message"][4:])
            if real_length != expected_length:
                raise ValueError(f"Mismatched message length: expected: {expected_length} got {real_length}")
            message = KdcReq.from_bytes(proxy_message["message"][4:])
        except Exception as exc:
            raise SuspiciousOperation from exc

        ctx = Context(
            request=request,
            message=message,
        )

        if isinstance(message, AsReq):
            rep = AsMessageHandler(ctx).handle()
        if isinstance(message, TgsReq):
            # return TgsMessageHandler(ctx).handle()
            raise NotImplementedError

        content = rep.to_bytes()
        response = KdcProxyMessage()
        response["message"] = len(content).to_bytes(4, byteorder="big") + content

        return HttpResponse(
            response.to_bytes(),
            content_type="application/kerberos",
        )
