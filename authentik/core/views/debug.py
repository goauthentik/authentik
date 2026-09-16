"""debug view"""

from http import HTTPStatus

from django.http import HttpRequest, HttpResponse
from django.views.generic import View
from drf_spectacular.utils import extend_schema
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from structlog.stdlib import get_logger

from authentik.api.validation import validate
from authentik.core.api.utils import PassiveSerializer
from authentik.policies.denied import AccessDeniedResponse

LOGGER = get_logger()


class AccessDeniedView(View):
    """Easily access AccessDeniedResponse"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        return AccessDeniedResponse(request)


class ServerLogAPI(APIView):
    """Debug-only endpoint to allow frontend to log messages, usable
    when browser develooper-tools aren't available.

    Never available in production."""

    class ServerLog(PassiveSerializer):

        message = CharField()

    serializer_class = ServerLog

    @extend_schema(
        responses={
            HTTPStatus.CREATED: None,
        }
    )
    @validate(ServerLog)
    def post(self, request: Request, body: ServerLog):
        LOGGER.debug(body.validated_data["message"])
        return Response(status=HTTPStatus.CREATED)
