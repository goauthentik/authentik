"""WebAuthn Related Origin Requests views"""

from django.http import Http404, HttpRequest, JsonResponse
from django.views import View

from authentik.stages.authenticator_webauthn.models import WebAuthnRPConfig


class WebAuthnRelatedOriginsView(View):
    """Serve the Related Origin Requests document (WebAuthn Level 3, §5.11).

    Browsers fetch https://<RP ID>/.well-known/webauthn when a WebAuthn ceremony
    is started from an origin whose host does not match the RP ID, to check
    whether that origin is authorized to use it."""

    def get(self, request: HttpRequest) -> JsonResponse:
        host = request.get_host().split(":")[0].lower()
        rp_config = WebAuthnRPConfig.objects.filter(rp_id=host).first()
        if not rp_config:
            raise Http404
        # The document format only supports web origins; other origin types
        # (e.g. android:apk-key-hash:) are validated server-side only.
        origins = [origin for origin in rp_config.origins if origin.startswith("https://")]
        response = JsonResponse({"origins": origins})
        response["Cache-Control"] = "max-age=300"
        # The body depends on the request host, not only the path
        response["Vary"] = "Host"
        return response
