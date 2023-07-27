"""authentik Kerberos views"""
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
    KdcReq,
    KrbError,
    TgsRep,
    TgsReq,
)
from authentik.providers.kerberos.models import KerberosProvider, KerberosRealm

LOGGER = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
class KdcProxyView(View):
    def as_req(self, req: AsReq) -> AsRep | KrbError:
        raise NotImplemented

    def tgs_req(self, req: TgsReq) -> TgsRep | KrbError:
        raise NotImplemented

    def post(self, request: HttpRequest, **kwargs) -> HttpResponse:
        self.request = request

        # TODO: catch exceptions and return kerberos error
        proxy_message = KdcProxyMessage.from_bytes(request.body)
        message = KdcReq.from_bytes(proxy_message["message"])
        # Might still be None
        self.realm = KerberosRealm.objects.filter(
            name=proxy_message.getComponentByName("target-domain", None)
        ).first()

        # TODO: catch exceptions and return kerberos error
        if isinstance(message, AsReq):
            return self.as_req(message)
        if isinstance(message, TgsReq):
            return self.tgs_req(message)

        # TODO: return kerberos error
        return HttpResponse({})
