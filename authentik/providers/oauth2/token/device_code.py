from django.http import HttpRequest

from authentik.common.oauth.constants import SCOPE_BOUND_KEY
from authentik.providers.oauth2.errors import DeviceCodeError, TokenError
from authentik.providers.oauth2.models import DeviceToken
from authentik.providers.oauth2.token.base import TokenRequest


class DeviceCodeTokenRequest(TokenRequest):

    device_code: DeviceToken | None = None

    def parse(self, request: HttpRequest) -> None:
        super().parse(request)
        device_code = request.POST.get("device_code", "")
        # Look up including expired codes so an expired code can be told apart from an
        # unknown one, see https://datatracker.ietf.org/doc/html/rfc8628#section-3.5
        code = (
            DeviceToken.objects.including_expired()
            .filter(device_code=device_code, provider=self.provider)
            .first()
        )
        if not code:
            raise TokenError("invalid_grant")
        if code.expires and code.is_expired:
            raise DeviceCodeError("expired_token")
        self.device_code = code

        if SCOPE_BOUND_KEY in self.device_code.scope:
            self.validate_dpop(
                request,
                self.device_code.dpop_jkt,
                raw_code=device_code,
                flow_name="device code",
            )
