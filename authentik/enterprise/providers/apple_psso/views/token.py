from pprint import pprint

from django.http import Http404, HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from jwcrypto.common import json_encode
from jwcrypto.jwe import JWE
from jwcrypto.jwk import JWK
from jwt import PyJWT, decode

from authentik.enterprise.providers.apple_psso.models import AppleDevice, ApplePlatformSSOProvider


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(View):

    def post(self, request: HttpRequest) -> HttpResponse:
        version = request.POST.get("platform_sso_version")
        print(version)
        assertion = request.POST.get("assertion", request.POST.get("request"))
        if not assertion:
            return HttpResponse(status=400)

        decode_unvalidated = PyJWT().decode_complete(assertion, options={"verify_signature": False})
        expected_kid = decode_unvalidated["header"]["kid"]

        device = AppleDevice.objects.filter(sign_key_id=expected_kid).first()
        if not device:
            raise Http404

        # Properly decode the JWT with the key from the device
        decoded = decode(
            assertion, device.signing_key, algorithms=["ES256"], options={"verify_aud": False}
        )
        pprint(decoded)
        return HttpResponse(status=400)
