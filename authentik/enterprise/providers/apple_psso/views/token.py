from datetime import timedelta

from django.http import Http404, HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from jwt import PyJWT, decode
from rest_framework.exceptions import ValidationError
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, Session, User
from authentik.core.sessions import SessionStore
from authentik.enterprise.providers.apple_psso.http import JWEResponse
from authentik.enterprise.providers.apple_psso.models import (
    AppleDevice,
    AppleDeviceUser,
    AppleNonce,
    ApplePlatformSSOProvider,
)
from authentik.providers.oauth2.constants import TOKEN_TYPE
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import RefreshToken
from authentik.root.middleware import SessionMiddleware

LOGGER = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(View):

    device: AppleDevice
    provider: ApplePlatformSSOProvider

    def post(self, request: HttpRequest) -> HttpResponse:
        version = request.POST.get("platform_sso_version")
        assertion = request.POST.get("assertion", request.POST.get("request"))
        if not assertion:
            return HttpResponse(status=400)

        decode_unvalidated = PyJWT().decode_complete(assertion, options={"verify_signature": False})
        LOGGER.debug(decode_unvalidated["header"])
        expected_kid = decode_unvalidated["header"]["kid"]

        self.device = AppleDevice.objects.filter(sign_key_id=expected_kid).first()
        if not self.device:
            raise Http404
        self.provider = self.device.provider

        # Properly decode the JWT with the key from the device
        decoded = decode(
            assertion, self.device.signing_key, algorithms=["ES256"], options={"verify_aud": False}
        )
        LOGGER.debug(decoded)

        LOGGER.debug("got device", device=self.device)

        # Check that the nonce hasn't been used before
        nonce = AppleNonce.objects.filter(nonce=decoded["request_nonce"]).first()
        if not nonce:
            return HttpResponse(status=400)
        nonce.delete()

        handler_func = (
            f"handle_v{version}_{decode_unvalidated["header"]["typ"]}".replace("-", "_")
            .replace("+", "_")
            .replace(".", "_")
        )
        handler = getattr(self, handler_func, None)
        if not handler:
            LOGGER.debug("Handler not found", handler=handler_func)
            return HttpResponse(status=400)
        LOGGER.debug("sending to handler", handler=handler_func)
        return handler(decoded)

    def validate_device_user_response(self, assertion: str) -> tuple[AppleDeviceUser, dict] | None:
        """Decode an embedded assertion and validate it by looking up the matching device user"""
        decode_unvalidated = PyJWT().decode_complete(assertion, options={"verify_signature": False})
        expected_kid = decode_unvalidated["header"]["kid"]

        device_user = AppleDeviceUser.objects.filter(
            device=self.device, enclave_key_id=expected_kid
        ).first()
        if not device_user:
            return None
        return device_user, decode(
            assertion,
            device_user.secure_enclave_key,
            audience="apple-platform-sso",
            algorithms=["ES256"],
        )

    def create_auth_session(self, user: User):
        store = SessionStore()
        store.save()
        session = Session.objects.filter(session_key=store.session_key).first()
        AuthenticatedSession.objects.create(
            session=session,
            user=user
        )
        session = SessionMiddleware.encode_session(store.session_key, user)
        return session

    def handle_v1_0_platformsso_login_request_jwt(self, decoded: dict):
        user = None
        if decoded["grant_type"] == "urn:ietf:params:oauth:grant-type:jwt-bearer":
            # Decode and validate inner assertion
            user, inner = self.validate_device_user_response(decoded["assertion"])
            if inner["nonce"] != decoded["nonce"]:
                LOGGER.warning("Mis-matched nonce to outer assertion")
                raise ValidationError("Invalid request")

        refresh_token = RefreshToken(
            user=user.user,
            scope=decoded["scope"],
            expires=now() + timedelta(hours=8),
            provider=self.provider,
            auth_time=now(),
            session=None,
        )
        id_token = IDToken.new(
            self.provider,
            refresh_token,
            self.request,
        )
        id_token.nonce = decoded["nonce"]
        refresh_token.id_token = id_token
        refresh_token.save()
        return JWEResponse(
            {
                "refresh_token": refresh_token.token,
                "refresh_token_expires_in": int((refresh_token.expires - now()).total_seconds()),
                "id_token": refresh_token.id_token.to_jwt(self.provider),
                "token_type": TOKEN_TYPE,
                "session_key": self.create_auth_session(user.user),
            },
            device=self.device,
            apv=decoded["jwe_crypto"]["apv"],
        )
