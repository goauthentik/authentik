from hashlib import sha256
from hmac import compare_digest
from http.cookies import Morsel
from json import dumps
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from jwt import PyJWTError, decode_complete
from structlog.stdlib import get_logger

from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import JWTAlgorithms

SESSION_KEY_DBSC_CHALLENGE = "goauthentik.io/stages/user_login/dbsc/challenge"
HEADER_DSBC_REGISTRATION = "Secure-Session-Registration"
HEADER_DBSC_RESPONSE = "Secure-Session-Response"
DBSC_ALGS = [JWTAlgorithms.ES256, JWTAlgorithms.RS256]
DBSC_COOKIE_NAME = "ak_tk"

LOGGER = get_logger()


def cookie_to_attrs(cookie: Morsel) -> str:
    """Convert a cookie to its attributes in a string form (without expiry attributes and
    without name and value)"""
    cookie_clone: Morsel = cookie.copy()
    cookie_clone.pop("expires", None)
    cookie_clone.pop("max-age", None)
    return (
        cookie_clone.OutputString()
        # Remove cookie name and value
        .replace(f"{cookie_clone.key}={cookie_clone.value}", "")
        # Remove leading semicolon
        .lstrip(";")
        # Remove surrounding spaces
        .strip()
    )


def set_dbsc_reg_header(request: HttpRequest, response: HttpResponse):
    """Generate Device-bound session credentials challenge and set header"""
    challenge = generate_id()
    request.session[SESSION_KEY_DBSC_CHALLENGE] = challenge
    dbsc_start_url = reverse("authentik_api:dbsc-start")
    response[HEADER_DSBC_REGISTRATION] = (
        f'({" ".join(DBSC_ALGS)}); path="{dbsc_start_url}"; challenge="{challenge}"'
    )
    return response

def validate_dbsc_challenge(request: HttpRequest) -> dict[str, Any]:
    """Validate Device-bound session credentials"""
    response = request.headers.get(HEADER_DBSC_RESPONSE)
    if not response:
        raise ValueError()
    try:
        decoded = decode_complete(
            response,
            algorithms=DBSC_ALGS,
            options={"verify_signature": False},
        )
    except PyJWTError as exc:
        LOGGER.warning("Invalid DBSC jwt", exc=exc)
        raise ValueError() from None
    if decoded["header"]["typ"] != "dbsc+jwt":
        LOGGER.warning("DBSC JWT with incorrect typ")
        raise ValueError()
    if not compare_digest(
        request.session[SESSION_KEY_DBSC_CHALLENGE], decoded["payload"]["jti"]
    ):
        LOGGER.warning("DBSC challenge mismatch")
        raise ValueError()
    return decoded


@method_decorator(csrf_exempt, name="dispatch")
class DeviceBoundSessionCredentailsStart(LoginRequiredMixin, View):
    def post(self, request: HttpRequest):
        try:
            validate_dbsc_challenge(request)
        except ValueError:
            return HttpResponseBadRequest()
        LOGGER.info("Registered for device-bound session credentials")
        response = HttpResponse(content_type="application/json")
        response["Cache-Control"] = "no-store"
        response.set_cookie(
            DBSC_COOKIE_NAME,
            "foo",
            10,
            path=settings.SESSION_COOKIE_PATH,
            domain=settings.SESSION_COOKIE_DOMAIN,
            httponly=True,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )
        response.content = dumps(
            {
                "session_identifier": sha256(
                    self.request.session.session_key.encode("ascii")
                ).hexdigest(),
                "refresh_url": reverse("authentik_api:dbsc-refresh"),
                "scope": {
                    "origin": request._current_scheme_host,
                    "include_site": False,
                },
                "credentials": [
                    {
                        "type": "cookie",
                        "name": DBSC_COOKIE_NAME,
                        "attributes": cookie_to_attrs(response.cookies[DBSC_COOKIE_NAME]),
                    }
                ],
            }
        )
        return response


@method_decorator(csrf_exempt, name="dispatch")
class DeviceBoundSessionCredentialRefresh(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return JsonResponse({"continue": False})
        print(request.GET)
        print(request.POST)
        print(request.headers)
        return HttpResponse()
