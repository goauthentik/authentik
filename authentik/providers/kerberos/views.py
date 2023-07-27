"""authentik Kerberos views"""
from dataclasses import dataclass

from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.lib.kerberos.protocol import (
    AsRep,
    AsReq,
    KdcProxyMessage,
    KdcRep,
    KdcReq,
    KrbError,
    TgsRep,
    TgsReq,
    PaData,
)
from authentik.providers.kerberos.models import KerberosProvider, KerberosRealm

LOGGER = get_logger()


@dataclass
class Context:
    request: HttpRequest
    message: KdcReq

class PaHandler:
    def __init__(self, ctx: Context):
        self.ctx = ctx

    def pre_validate(self):
        raise NotImplemented

    def validate(self) -> PaData
        raise NotImplemented

    def post_validate(self):
        raise NotImplemented

class PaEncTimestampHandler(PaHandler):
    pass


class MessageHandler:
    PREAUTH_HANDLERS = []

    def __init__(self, ctx: Context):
        self.ctx = ctx

    def pre_validate(self) -> KrbError:
        for handler in PREAUTH_HANDLERS:
            handler.pre_validate()

    def query_pre_validate(self):
        raise NotImplemented

    def validate_ticket_request(self):
        raise NotImplemented

    def handle(self) -> KdcRep | KrbError:
        self.pre_validate()
        self.query_pre_validate()
        self.pre_auth()
        return self.execute()

class AsMessageHandler(MessageHandler):
    PREAUTH_HANDLERS = [
        PaEncTimestampHandler,
    ]

    def execute(self) -> KdcRep | KrbError:
        pass

    def query_pre_validate(self):
        # TODO: check realm and principal exists
        raise NotImplemented


@method_decorator(csrf_exempt, name="dispatch")
class KdcProxyView(View):
    def post(self, request: HttpRequest, **kwargs) -> HttpResponse:
        # TODO: catch exceptions and return kerberos error
        proxy_message = KdcProxyMessage.from_bytes(request.body)
        message = KdcReq.from_bytes(proxy_message["message"])
        # Might still be None
        self.realm = KerberosRealm.objects.filter(
            name=proxy_message.getComponentByName("target-domain", None)
        ).first()

        # TODO: catch exceptions and return kerberos error
        if isinstance(message, AsReq):
            rep = AsMessageHandler(Context(request=request, message=message)).handle()
        if isinstance(message, TgsReq):
            #return TgsMessageHandler(Context(request=request, message=message)).handle()
            raise NotImplemented

        return HttpResponse(
            rep.to_bytes(),
            content_type="application/kerberos",
        )
