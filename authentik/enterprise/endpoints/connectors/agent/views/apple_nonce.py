from base64 import b64encode
from datetime import timedelta
from secrets import token_bytes
from urllib.parse import unquote

from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from authentik.endpoints.connectors.agent.models import AppleNonce, DeviceToken


@method_decorator(csrf_exempt, name="dispatch")
class NonceView(View):

    def post(self, request: HttpRequest, *args, **kwargs):
        raw_token = unquote(self.request.POST.get("x-ak-device-token"))
        device_token = DeviceToken.objects.filter(key=raw_token).first()
        if not device_token:
            return HttpResponseBadRequest()
        nonce = AppleNonce.objects.create(
            nonce=b64encode(token_bytes(32)).decode(),
            expires=now() + timedelta(minutes=5),
            device_token=device_token,
        )
        return JsonResponse(
            {
                "Nonce": nonce.nonce,
            }
        )
