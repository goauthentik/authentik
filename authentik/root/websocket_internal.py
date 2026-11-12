"""Internal endpoints for the WebSocket routes the Rust server serves itself.

When a route is enabled in ``web.rust_websocket_routes``, the Rust server terminates the
WebSocket instead of relaying it to Django Channels. It still asks Python whether to accept
each connection and which channel layer groups to join, so authorization keeps a single
implementation. Messages keep flowing through the PostgreSQL channel layer, which the Rust
server reads like any other consumer.

The Rust server owns every path under ``/-/`` and never forwards one, so these views are only
reachable from it, over gunicorn's unix socket. They are not part of the public API schema.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from http.cookies import CookieError
from json import JSONDecodeError, loads

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.http.cookie import parse_cookie
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.fields import CharField, ChoiceField, DictField
from structlog.stdlib import get_logger

from authentik.core.api.utils import PassiveSerializer
from authentik.events.consumer import build_user_group
from authentik.root.asgi_middleware import user_from_session_cookie

LOGGER = get_logger()


@dataclass(slots=True)
class WebsocketAuthorization:
    """Whether to accept a WebSocket connection, and the channel layer groups it joins."""

    accept: bool
    groups: list[str] = field(default_factory=list)


def authorize_client(headers: dict[str, str]) -> WebsocketAuthorization:
    """`/ws/client/`: logged-in users receive their notifications.

    Mirrors `authentik.events.consumer.ClientConsumer.connect`."""
    try:
        cookies = parse_cookie(headers.get("cookie", ""))
    except CookieError:
        cookies = {}
    user = user_from_session_cookie(cookies.get(settings.SESSION_COOKIE_NAME))
    if not user.is_authenticated:
        return WebsocketAuthorization(accept=False)
    return WebsocketAuthorization(accept=True, groups=[build_user_group(user)])


AUTHORIZERS: dict[str, Callable[[dict[str, str]], WebsocketAuthorization]] = {
    "client": authorize_client,
}


class WebsocketAuthorizeRequestSerializer(PassiveSerializer):
    """A WebSocket handshake the Rust server received.

    Header names are lowercase. The Rust server decodes values that aren't valid UTF-8 the way
    the ASGI middleware does, with backslash escapes."""

    route = ChoiceField(choices=sorted(AUTHORIZERS))
    path = CharField()
    headers = DictField(
        child=CharField(allow_blank=True, trim_whitespace=False), required=False, default=dict
    )


@method_decorator(csrf_exempt, name="dispatch")
class WebsocketAuthorizeView(View):
    """Authorize a WebSocket handshake for the Rust server."""

    http_method_names = ["post"]

    def post(self, request: HttpRequest) -> HttpResponse:
        try:
            body = loads(request.body)
        except JSONDecodeError, UnicodeDecodeError:
            return HttpResponseBadRequest()
        serializer = WebsocketAuthorizeRequestSerializer(data=body)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=400)
        route: str = serializer.validated_data["route"]
        headers: dict[str, str] = serializer.validated_data["headers"]
        authorization = AUTHORIZERS[route](headers)
        # Same fields as `ChannelsLoggingMiddleware`, which logs connections Channels serves.
        LOGGER.info(
            serializer.validated_data["path"],
            scheme="ws",
            remote=headers.get("x-forwarded-for", ""),
            user_agent=headers.get("user-agent", ""),
            accepted=authorization.accept,
        )
        return JsonResponse(asdict(authorization))
