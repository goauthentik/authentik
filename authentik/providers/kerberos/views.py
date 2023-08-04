"""authentik Kerberos views"""

from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.providers.kerberos.lib import crypto, iana, protocol
from authentik.providers.kerberos.lib.exceptions import KerberosError
from authentik.providers.kerberos.models import KerberosProvider, KerberosRealm
from authentik.providers.kerberos import kdc

LOGGER = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
class KdcProxyView(View):
    def post(self, request: HttpRequest, realm_name: str, **kwargs) -> HttpResponse:
        realm = get_object_or_404(KerberosRealm, realm_name=realm_name)
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
