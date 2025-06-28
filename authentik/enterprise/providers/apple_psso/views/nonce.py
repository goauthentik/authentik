from base64 import b64encode
from datetime import timedelta
from secrets import token_bytes

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from authentik.enterprise.providers.apple_psso.models import AppleNonce


@method_decorator(csrf_exempt, name="dispatch")
class NonceView(View):

    def post(self, request: HttpRequest, *args, **kwargs):
        nonce = AppleNonce.objects.create(
            nonce=b64encode(token_bytes(32)).decode(), expires=now() + timedelta(minutes=5)
        )
        return JsonResponse(
            {
                "Nonce": nonce.nonce,
            }
        )
