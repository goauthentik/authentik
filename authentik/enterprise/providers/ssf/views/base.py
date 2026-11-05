from django.http import Http404, HttpRequest
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import Application
from authentik.enterprise.providers.ssf.models import SSFProvider, Stream, StreamStatus
from authentik.enterprise.providers.ssf.views.auth import SSFTokenAuth


class SSFView(APIView):
    application: Application
    provider: SSFProvider
    logger: BoundLogger

    permission_classes = [IsAuthenticated]

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        self.logger = get_logger().bind()
        super().setup(request, *args, **kwargs)

    def get_authenticators(self):
        return [SSFTokenAuth(self)]


class SSFStreamView(SSFView):
    def get_object(self) -> Stream:
        streams = Stream.objects.filter(provider=self.provider).exclude(
            status=StreamStatus.DISABLED_DELETED
        )
        if "stream_id" in self.request.query_params:
            streams = streams.filter(pk=self.request.query_params["stream_id"])
        if "stream_id" in self.request.data:
            streams = streams.filter(pk=self.request.data["stream_id"])
        stream = streams.first()
        if not stream:
            raise Http404()
        return stream
