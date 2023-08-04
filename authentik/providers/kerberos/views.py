"""authentik Kerberos views"""

from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.api.authentication import bearer_auth
from authentik.outposts.models import Outpost
from authentik.providers.kerberos import kdc
from authentik.providers.kerberos.lib import protocol
from authentik.providers.kerberos.models import KerberosRealm

LOGGER = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
class KdcProxyView(View):
    def post(self, request: HttpRequest, realm_name: str, **kwargs) -> HttpResponse:
        realm = get_object_or_404(KerberosRealm, realm_name=realm_name)

        self.remote_addr = request.META["REMOTE_ADDR"]
        if "X-Outpost-RemoteAddr" in request.headers:
            if not "Authorization" in request.headers:
                raise SuspiciousOperation()
            user = bearer_auth(request.headers["Authorization"].encode())
            if not user:
                raise SuspiciousOperation()
            associated_outpost = None
            for outpost in Outpost.objects.filter(providers__pk=realm.pk):
                if outpost.user == user:
                    associated_outpost = outpost
                    break
            if not associated_outpost:
                raise SuspiciousOperation()

            self.remote_addr = request.headers["X-Outpost-RemoteAddr"]

        try:
            proxy_message = protocol.KdcProxyMessage.from_bytes(request.body).to_python()
            expected_length, message = proxy_message["message"]
            if len(message) != expected_length:
                raise ValueError(
                    f"Mismatched message length: expected: {expected_length} got {len(message)}"
                )
            if "target-domain" not in proxy_message:
                raise ValueError("Missing target-domain")
            if proxy_message["target-domain"] != realm.realm_name:
                raise ValueError(
                    f"Mismatched realm name: expected: {realm.realm_name} got {proxy_message['target-domain']}"
                )
            handler = kdc.KdcReqMessageHandler.from_message(
                view=self,
                message=message,
                realm=realm,
            )
        except Exception as exc:
            raise SuspiciousOperation from exc

        content = handler.handle().to_bytes()
        response = protocol.KdcProxyMessage().from_python({"message": (len(content), content)})

        return HttpResponse(
            response.to_bytes(),
            content_type="application/kerberos",
        )
