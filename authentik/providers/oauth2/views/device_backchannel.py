"""Device flow views"""

from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.throttling import AnonRateThrottle
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.lib.config import CONFIG
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.errors import DeviceCodeError
from authentik.providers.oauth2.models import DeviceToken, OAuth2Provider
from authentik.providers.oauth2.utils import TokenResponse
from authentik.providers.oauth2.views.device_init import QS_KEY_CODE

LOGGER = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
class DeviceView(View):
    """Device flow, devices can request tokens which users can verify"""

    client_id: str
    provider: OAuth2Provider
    scopes: list[str] = []

    def parse_request(self):
        """Parse incoming request"""
        client_id = self.request.POST.get("client_id", None)
        if not client_id:
            raise DeviceCodeError("invalid_client")
        provider = OAuth2Provider.objects.filter(client_id=client_id).first()
        if not provider:
            raise DeviceCodeError("invalid_client")
        try:
            _ = provider.application
        except Application.DoesNotExist:
            raise DeviceCodeError("invalid_client") from None
        self.provider = provider
        self.client_id = client_id
        self.scopes = self.request.POST.get("scope", "").split(" ")

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        throttle = AnonRateThrottle()
        throttle.rate = CONFIG.get("throttle.providers.oauth2.device", "20/hour")
        throttle.num_requests, throttle.duration = throttle.parse_rate(throttle.rate)
        if not throttle.allow_request(request, self):
            return TokenResponse(DeviceCodeError("slow_down").create_dict(request), status=429)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Generate device token"""
        try:
            self.parse_request()
        except DeviceCodeError as exc:
            return TokenResponse(exc.create_dict(request), status=400)
        until = timedelta_from_string(self.provider.access_code_validity)
        token: DeviceToken = DeviceToken.objects.create(
            expires=now() + until, provider=self.provider, _scope=" ".join(self.scopes)
        )
        device_url = self.request.build_absolute_uri(
            reverse("authentik_providers_oauth2_root:device-login")
        )
        return TokenResponse(
            {
                "device_code": token.device_code,
                "verification_uri": device_url,
                "verification_uri_complete": (
                    device_url
                    + "?"
                    + urlencode(
                        {
                            QS_KEY_CODE: token.user_code,
                        }
                    )
                ),
                "user_code": token.user_code,
                "expires_in": int(until.total_seconds()),
                "interval": 5,
            }
        )
